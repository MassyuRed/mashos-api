# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal special-case material for EmlisAI state answers.

Phase 5 materializes the guarded handling for self-denial and anger described
by the state-answer design.  The material is internal/meta-only: it separates a
felt state from an identity claim, permits only a limited Emlis counter-opinion
when input evidence is present, and blocks anger target-judgement agreement
while allowing inner-value-line receiving.

This module does not create user-facing ``comment_text``, does not add public
response keys, does not alter API routes, DB physical names, or RN display
conditions, and does not store raw input or visible surface bodies in reports.
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

EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION: Final = (
    "cocolon.emlis_ai_state_answer_special_cases.v1"
)
EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID: Final = "emlis_ai_state_answer_special_cases"
EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE: Final = "Phase5_self_denial_and_anger_special_handling"
EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_INTERNAL_NAME: Final = (
    "EmlisAI状態回答 自己否定・怒りSpecial Handling"
)

_SPACE_RE: Final = re.compile(r"\s+")
_SELF_DENIAL_RE: Final = re.compile(
    r"(自分(?:なんか|など|は|が|を|だけ)?[^。！？!?\n]{0,36}(?:嫌い|きらい|ダメ|だめ|駄目|価値がない|価値ない|いらない|最低|クズ|消えたい|死にたい|生きてる意味|生きる意味|責め|追い込|下げ|続けられない人間|何もできていない|できない)|"
    r"(?:私|わたし|俺|僕)(?:なんか|など|は|が)?[^。！？!?\n]{0,32}(?:嫌い|きらい|ダメ|だめ|駄目|価値がない|価値ない|いらない|最低|クズ|消えたい|死にたい|悪い|できない)|"
    r"できない自分|自分だけ[^。！？!?\n]{0,24}何もでき|(?:全部|すべて|みんな)(?:自分|私|わたし|俺|僕)が悪い)"
)
_ANGER_RE: Final = re.compile(
    r"(怒り|怒っ|腹が立|腹立|ムカつ|むかつ|イライラ|いらいら|許せない|理不尽|不公平|納得できない|軽く扱われ)"
)

# In-memory visible-surface guard patterns.  These are classifiers only; they
# are never inserted into runtime output.
_SELF_DENIAL_ALLOWED_COUNTER_RE: Final = re.compile(
    r"(Emlis[^。！？!?\n]{0,24}(?:そうは見えません|そのまま受け取りません|見えません)|"
    r"(?:その言葉|その自己否定|その一言)[^。！？!?\n]{0,40}(?:全体を決め|決めてよい|決めていい)[^。！？!?\n]{0,24}(?:見えません|扱いません)|"
    r"(?:言葉そのものの人|言葉だけであなた全体)[^。！？!?\n]{0,30}(?:見えません|扱いません))"
)
_SELF_DENIAL_FORBIDDEN_OVER_COMFORT_RE: Final = re.compile(
    r"(あなたは(?:素晴らしい|優しい人|弱い人ではありません|本当は強い|絶対に悪くありません|絶対悪くありません|悪くないです)|"
    r"(?:もう大丈夫|必ず良く|必ずよく|安心してください|何があっても味方|絶対味方|全部受け止めます|あなたは絶対))"
)
_SELF_DENIAL_IDENTITY_ACCEPTANCE_RE: Final = re.compile(
    r"(あなたは(?:ダメ|だめ|駄目|価値がない|最低|クズ)|その言葉どおりの人|自己否定の通り)"
)
_ANGER_TARGET_JUDGEMENT_RE: Final = re.compile(
    r"((?:相手|上司|あの人|その人|彼|彼女|会社|職場)[^。！？!?\n]{0,22}(?:悪い|ひどい|最低|おかしい|間違って|軽く見て|見下して|敵)|"
    r"あなたの怒りは(?:正しい|当然)|"
    r"そんな人(?:とは|から)[^。！？!?\n]{0,24}(?:距離|離れ)|"
    r"(?:距離を取った方がいい|離れた方がいい|関わらない方がいい))"
)
_ANGER_ATTACK_AMPLIFICATION_RE: Final = re.compile(
    r"(仕返し|言い返してや|攻撃|許さなくていい|相手を責め|相手に分からせ|潰し|やり返)"
)
_ANGER_INNER_VALUE_LINE_RE: Final = re.compile(
    r"(大事にしていた線|納得できない扱われ方|不公平感|軽く扱われた感覚|越えられたように|大切にしていたもの)"
)

_FORBIDDEN_PAYLOAD_KEYS: Final = frozenset(
    {
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
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
        "body",
        "text",
        "sentence",
        "sentences",
        "phrase",
        "raw_quote",
        "raw_quotes",
        "evidence_text",
        "matched_raw_quote_fragments",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "api_response_key_change",
        "comment_text_body_included",
        "comment_text_generated",
        "comment_text_included",
        "completed_reply_generated",
        "db_physical_name_changed",
        "display_gate_relaxed",
        "external_ai_used",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "gate_relaxed",
        "input_specific_template_used",
        "local_llm_used",
        "public_payload_changed",
        "public_response_key_added",
        "public_response_key_change",
        "raw_input_included",
        "raw_text_included",
        "response_key_changed",
        "rn_visible_contract_changed",
        "schema_file_materialized",
        "target_judgement_agreement_allowed",
        "target_attack_amplification_allowed",
        "identity_claim_as_fact_allowed",
        "blanket_personality_praise_allowed",
        "absolute_support_or_alliance_allowed",
        "over_comfort_allowed",
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
    if isinstance(value, (str, bytes)):
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


def _current_source_summary(current_source: Any) -> dict[str, Any]:
    data = _as_mapping(current_source)
    source_id = _clean(data.get("id") or data.get("record_id") or data.get("source_record_id"))
    selected_at = _clean(data.get("created_at") or data.get("selected_at"))
    return {
        "source_kind": "current_input",
        "source_record_id": source_id,
        "selected_at": selected_at,
    }


def _current_source_text(current_source: Any) -> str:
    data = _as_mapping(current_source)
    parts: list[str] = []
    for key in ("memo", "memo_action"):
        text = _clean(data.get(key))
        if text:
            parts.append(text)
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


def _emotion_labels(current_source: Any) -> list[str]:
    data = _as_mapping(current_source)
    out: list[str] = []
    for item in _listify(data.get("emotion_details")):
        if isinstance(item, Mapping):
            out.append(_clean(item.get("type")))
        else:
            out.append(_clean(item))
    for item in _listify(data.get("emotions")):
        out.append(_clean(item))
    return _dedupe(out)


def _coerce_frame(current_source: Any, environment_state_output_frame: Any = None) -> dict[str, Any]:
    frame = _as_mapping(environment_state_output_frame)
    if frame:
        return copy.deepcopy(dict(frame))
    built = build_environment_state_output_frame(current_source or {})
    return copy.deepcopy(dict(built.as_meta() if hasattr(built, "as_meta") else built))


def _span_ids_for_fields(frame: Mapping[str, Any], *fields: str) -> list[str]:
    wanted = {field for field in fields if field}
    out: list[str] = []

    # Full environment_state_output_frame keeps detailed span objects.  The
    # Phase 2 state-answer projection keeps only text-free ids by axis; support
    # both so Phase 5 can be connected without reintroducing raw text.
    if "memo" in wanted:
        out.extend(_dedupe(_as_mapping(frame.get("output_axis")).get("thought_evidence_span_ids") or []))
    if "memo_action" in wanted:
        out.extend(_dedupe(_as_mapping(frame.get("environment_axis")).get("action_evidence_span_ids") or []))
    if "emotion_details" in wanted or "emotions" in wanted:
        for label in _as_mapping(frame.get("state_axis")).get("emotion_labels") or []:
            if isinstance(label, Mapping):
                out.extend(_dedupe(label.get("evidence_span_ids") or []))

    spans = _as_mapping(frame.get("evidence")).get("spans") or []
    for span in spans:
        if not isinstance(span, Mapping):
            continue
        if _clean(span.get("source_field")) not in wanted:
            continue
        span_id = _clean(span.get("span_id"))
        if span_id:
            out.append(span_id)
    return _dedupe(out)


def _all_evidence_span_ids(frame: Mapping[str, Any]) -> list[str]:
    ids = _dedupe(_as_mapping(frame.get("evidence")).get("evidence_span_ids") or [])
    ids.extend(_span_ids_for_fields(frame, "memo", "memo_action", "emotion_details", "emotions"))
    spans = _as_mapping(frame.get("evidence")).get("spans") or []
    ids.extend(span.get("span_id") for span in spans if isinstance(span, Mapping))
    for item in _as_mapping(frame.get("output_axis")).get("output_theme_candidates") or []:
        if isinstance(item, Mapping):
            ids.extend(_dedupe(item.get("evidence_span_ids") or []))
    return _dedupe(ids)


def _signal_summary(*, current_source: Any, frame: Mapping[str, Any]) -> dict[str, Any]:
    source_text = _current_source_text(current_source)
    labels = _emotion_labels(current_source)
    self_denial_by_text = bool(_SELF_DENIAL_RE.search(source_text))
    self_denial_by_emotion = any(label in {"自己否定", "自己嫌悪"} for label in labels)
    anger_by_text = bool(_ANGER_RE.search(source_text))
    anger_by_emotion = any(label == "怒り" for label in labels)
    return {
        "signal_source": "current_input_meta_only",
        "self_denial_detected": bool(self_denial_by_text or self_denial_by_emotion),
        "self_denial_detection_basis": _dedupe(
            [
                "self_denial_language_signal" if self_denial_by_text else "",
                "self_denial_emotion_label" if self_denial_by_emotion else "",
            ]
        ),
        "anger_detected": bool(anger_by_text or anger_by_emotion),
        "anger_detection_basis": _dedupe(
            [
                "anger_language_signal" if anger_by_text else "",
                "anger_emotion_label" if anger_by_emotion else "",
            ]
        ),
        "emotion_labels": labels,
        "evidence_span_ids": _all_evidence_span_ids(frame),
        "thought_evidence_span_ids": _span_ids_for_fields(frame, "memo"),
        "action_evidence_span_ids": _span_ids_for_fields(frame, "memo_action"),
        "emotion_evidence_span_ids": _span_ids_for_fields(frame, "emotion_details", "emotions"),
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _safe_layer_summary(value: Any) -> dict[str, Any]:
    data = _as_mapping(value)
    return {
        "schema_version": _clean(data.get("schema_version")),
        "material_id": _clean(data.get("material_id")),
        "source_phase": _clean(data.get("source_phase") or data.get("phase")),
        "input_type": _clean(data.get("input_type") or data.get("selector_input_type")),
        "primary_follow_key": _clean(data.get("primary_follow_key")),
        "secondary_follow_keys": _dedupe(data.get("secondary_follow_keys") or []),
        "afterglow_follow_key": _clean(data.get("afterglow_follow_key")),
        "resolved_ratio_reason": _clean(_as_mapping(data.get("resolved_ratio")).get("reason")),
        "resolved_ratio": {
            "observation": _as_mapping(data.get("resolved_ratio")).get("observation"),
            "human_follow": _as_mapping(data.get("resolved_ratio")).get("human_follow"),
        }
        if data.get("resolved_ratio")
        else {},
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _self_denial_policy(signal_summary: Mapping[str, Any]) -> dict[str, Any]:
    enabled = bool(signal_summary.get("self_denial_detected"))
    evidence_span_ids = _dedupe(
        signal_summary.get("thought_evidence_span_ids")
        or signal_summary.get("evidence_span_ids")
        or []
    )
    evidence_ready = bool(evidence_span_ids)
    limited_counter = bool(enabled and evidence_ready)
    return {
        "enabled": enabled,
        "special_case_id": "self_denial_identity_claim_boundary" if enabled else "self_denial_not_detected",
        "felt_state_is_real": bool(enabled),
        "felt_state_as_fact_allowed": bool(enabled),
        "identity_claim_is_not_accepted": bool(enabled),
        "identity_claim_as_fact_allowed": False,
        "emlis_impression_has_evidence": evidence_ready if enabled else False,
        "may_counter_identity_claim_as_emlis_impression": limited_counter,
        "limited_counter_opinion_allowed": limited_counter,
        "requires_input_evidence_for_counter_opinion": True,
        "must_separate_felt_state_from_identity_fact": True,
        "must_include_input_evidence": True,
        "evidence_required": True,
        "evidence_span_ids": evidence_span_ids,
        "allowed_exception_surface_claim_ids": [
            "felt_state_identity_claim_split",
            "limited_counter_opinion_about_identity_claim",
            "emlis_impression_not_identity_fact",
        ]
        if enabled
        else [],
        "forbidden_surface_claim_ids": [
            "identity_claim_accepted_as_fact",
            "blanket_personality_praise",
            "absolute_support_or_alliance",
            "absolute_denial_without_evidence",
            "over_comfort",
        ],
        "self_denial_content_should_not_be_left_unhandled": bool(enabled),
        "blanket_personality_praise_allowed": False,
        "absolute_support_or_alliance_allowed": False,
        "over_comfort_allowed": False,
        "absolute_denial_allowed": False,
        "personality_claim_allowed": False,
        "completed_reply_generated": False,
        "raw_text_included": False,
    }


def _anger_policy(signal_summary: Mapping[str, Any]) -> dict[str, Any]:
    enabled = bool(signal_summary.get("anger_detected"))
    evidence_span_ids = _dedupe(
        signal_summary.get("thought_evidence_span_ids")
        or signal_summary.get("action_evidence_span_ids")
        or signal_summary.get("evidence_span_ids")
        or []
    )
    return {
        "enabled": enabled,
        "special_case_id": "anger_inner_value_line_boundary" if enabled else "anger_not_detected",
        "target_judgement_agreement_allowed": False,
        "anger_target_judgement_agreement_allowed": False,
        "target_attack_amplification_allowed": False,
        "must_not_agree_with_target_judgement": True,
        "may_receive_inner_value_line": True,
        "inner_value_line_receiving_allowed": bool(enabled),
        "anger_state_may_be_observed": bool(enabled),
        "evidence_span_ids": evidence_span_ids,
        "allowed_surface_claim_ids": [
            "anger_felt_state_observation",
            "inner_value_line_receiving",
            "unfairness_sense_without_target_fact",
        ]
        if enabled
        else [],
        "forbidden_surface_claim_ids": [
            "target_is_bad_fact_claim",
            "target_intent_claim",
            "anger_is_correct_claim",
            "target_attack_amplification",
            "distance_instruction",
        ],
        "completed_reply_generated": False,
        "raw_text_included": False,
    }


def _gate_policy(self_denial: Mapping[str, Any], anger: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "special_cases_gate_policy_active": bool(self_denial.get("enabled") or anger.get("enabled")),
        "tone_engine_self_denial_exception_allowed": bool(self_denial.get("limited_counter_opinion_allowed")),
        "visible_gate_self_denial_exception_allowed": bool(self_denial.get("limited_counter_opinion_allowed")),
        "self_denial_exception_must_have_evidence": True,
        "self_denial_personality_praise_allowed": False,
        "self_denial_absolute_support_allowed": False,
        "anger_target_judgement_agreement_blocked": True,
        "anger_target_attack_amplification_blocked": True,
        "anger_inner_value_line_receiving_allowed": bool(anger.get("inner_value_line_receiving_allowed")),
        "target_judgement_agreement_allowed": False,
        "target_attack_amplification_allowed": False,
        "personality_claim_allowed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "comment_text_generated": False,
        "raw_text_included": False,
    }


@dataclass(frozen=True)
class EmlisStateAnswerSpecialCases:
    """Meta-only Phase 5 material for self-denial and anger handling."""

    source: Mapping[str, Any]
    signal_summary: Mapping[str, Any]
    self_denial: Mapping[str, Any]
    anger: Mapping[str, Any]
    gate_policy: Mapping[str, Any]
    environment_state_output_frame: Mapping[str, Any]
    human_follow_layer: Mapping[str, Any]
    ratio_policy: Mapping[str, Any]
    observation_structure_material: Mapping[str, Any]
    schema_version: str = EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION
    material_id: str = EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID
    internal_name: str = EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_INTERNAL_NAME
    phase: str = EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE
    passed: bool = True
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_meta(self) -> dict[str, Any]:
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
            "enabled_case_ids": _dedupe([
                "self_denial" if self.self_denial.get("enabled") else "",
                "anger" if self.anger.get("enabled") else "",
            ]),
            "source": _deepcopy_mapping(self.source),
            "signal_summary": _deepcopy_mapping(self.signal_summary),
            "self_denial": _deepcopy_mapping(self.self_denial),
            "anger": _deepcopy_mapping(self.anger),
            "gate_policy": _deepcopy_mapping(self.gate_policy),
            "environment_state_output_frame": _deepcopy_mapping(self.environment_state_output_frame),
            "human_follow_layer": _deepcopy_mapping(self.human_follow_layer),
            "ratio_policy": _deepcopy_mapping(self.ratio_policy),
            "observation_structure_material": _deepcopy_mapping(self.observation_structure_material),
            "surface_exception_policy": {
                "self_denial_limited_counter_opinion_allowed": bool(self.self_denial.get("limited_counter_opinion_allowed")),
                "self_denial_exception_requires_input_evidence": True,
                "self_denial_identity_claim_as_fact_allowed": False,
                "self_denial_personality_praise_allowed": False,
                "self_denial_absolute_support_allowed": False,
                "anger_target_judgement_agreement_blocked": True,
                "anger_target_attack_amplification_blocked": True,
                "anger_inner_value_line_receiving_allowed": bool(self.anger.get("inner_value_line_receiving_allowed")),
                "target_judgement_agreement_allowed": False,
                "target_attack_amplification_allowed": False,
                "comment_text_generated": False,
                "raw_text_included": False,
                "gate_relaxed": False,
            },
            "selector_context": {
                "self_denial_detected": bool(self.signal_summary.get("self_denial_detected")),
                "anger_detected": bool(self.signal_summary.get("anger_detected")),
                "human_follow_input_type": _clean(self.human_follow_layer.get("input_type")),
                "primary_follow_key": _clean(self.human_follow_layer.get("primary_follow_key")),
                "ratio_policy_reason": _clean(self.ratio_policy.get("resolved_ratio_reason")),
                "raw_text_included": False,
            },
            "state_answer_special_cases_connected": True,
            "state_answer_special_cases_material_only": True,
            "self_denial_special_handling_enabled": bool(self.self_denial.get("enabled")),
            "anger_special_handling_enabled": bool(self.anger.get("enabled")),
            "felt_state_is_real": bool(self.self_denial.get("felt_state_is_real")),
            "identity_claim_is_not_accepted": bool(self.self_denial.get("identity_claim_is_not_accepted")),
            "emlis_impression_has_evidence": bool(self.self_denial.get("emlis_impression_has_evidence")),
            "limited_counter_opinion_allowed": bool(self.self_denial.get("limited_counter_opinion_allowed")),
            "inner_value_line_receiving_allowed": bool(self.anger.get("inner_value_line_receiving_allowed")),
            "target_judgement_agreement_allowed": False,
            "target_attack_amplification_allowed": False,
            "identity_claim_as_fact_allowed": False,
            "blanket_personality_praise_allowed": False,
            "absolute_support_or_alliance_allowed": False,
            "over_comfort_allowed": False,
            "personality_claim_allowed": False,
            "completed_reply_generated": False,
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
            "gate_relaxed": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_state_answer_special_cases_contract(meta)
        return meta

    def gate_report(self) -> dict[str, Any]:
        meta = self.as_meta()
        report = {
            "schema_version": meta["schema_version"],
            "material_id": meta["material_id"],
            "source_phase": meta["source_phase"],
            "passed": bool(meta["passed"]),
            "evaluated": True,
            "status": meta["status"],
            "rejection_reasons": list(meta["rejection_reasons"]),
            "enabled_case_ids": list(meta.get("enabled_case_ids") or []),
            "state_answer_special_cases_connected": True,
            "state_answer_special_cases_material_only": True,
            "self_denial_special_handling_enabled": bool(meta["self_denial_special_handling_enabled"]),
            "anger_special_handling_enabled": bool(meta["anger_special_handling_enabled"]),
            "felt_state_is_real": bool(meta["felt_state_is_real"]),
            "identity_claim_is_not_accepted": bool(meta["identity_claim_is_not_accepted"]),
            "emlis_impression_has_evidence": bool(meta["emlis_impression_has_evidence"]),
            "limited_counter_opinion_allowed": bool(meta["limited_counter_opinion_allowed"]),
            "self_denial_counter_opinion_requires_evidence": True,
            "self_denial_identity_claim_as_fact_allowed": False,
            "self_denial_personality_praise_allowed": False,
            "self_denial_absolute_support_allowed": False,
            "anger_target_judgement_agreement_blocked": True,
            "anger_target_attack_amplification_blocked": True,
            "anger_inner_value_line_receiving_allowed": bool(meta["inner_value_line_receiving_allowed"]),
            "target_judgement_agreement_allowed": False,
            "target_attack_amplification_allowed": False,
            "personality_claim_allowed": False,
            "comment_text_generated": False,
            "raw_text_included": False,
            "display_gate_relaxed": False,
        }
        assert_state_answer_special_cases_contract(report)
        return report

    def composer_payload(self) -> dict[str, Any]:
        meta = self.as_meta()
        payload = {
            "schema_version": meta["schema_version"],
            "material_id": meta["material_id"],
            "source_phase": meta["source_phase"],
            "source": _deepcopy_mapping(meta.get("source")),
            "enabled_case_ids": list(meta.get("enabled_case_ids") or []),
            "self_denial": _deepcopy_mapping(_as_mapping(meta.get("self_denial"))),
            "anger": _deepcopy_mapping(_as_mapping(meta.get("anger"))),
            "gate_policy": _deepcopy_mapping(_as_mapping(meta.get("gate_policy"))),
            "state_answer_special_cases_connected": True,
            "state_answer_special_cases_material_only": True,
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "raw_text_included": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_state_answer_special_cases_contract(payload)
        return payload


def build_emlis_ai_state_answer_special_cases(
    current_input: Any = None,
    *,
    environment_state_output_frame: Any = None,
    observation_structure_material: Any = None,
    human_follow_layer: Mapping[str, Any] | None = None,
    ratio_policy: Mapping[str, Any] | None = None,
) -> EmlisStateAnswerSpecialCases:
    frame = _coerce_frame(current_input, environment_state_output_frame)
    signal = _signal_summary(current_source=current_input, frame=frame)
    self_denial = _self_denial_policy(signal)
    anger = _anger_policy(signal)
    gate_policy = _gate_policy(self_denial, anger)
    material = EmlisStateAnswerSpecialCases(
        source=_current_source_summary(current_input),
        signal_summary=signal,
        self_denial=self_denial,
        anger=anger,
        gate_policy=gate_policy,
        environment_state_output_frame={
            "material_id": _clean(frame.get("material_id")) or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
            "schema_version": _clean(frame.get("schema_version")),
            "axis_presence": _deepcopy_mapping(_as_mapping(frame.get("axis_presence"))),
            "evidence_span_ids": _all_evidence_span_ids(frame),
            "raw_text_included": False,
        },
        human_follow_layer=_safe_layer_summary(human_follow_layer),
        ratio_policy=_safe_layer_summary(ratio_policy),
        observation_structure_material=_safe_layer_summary(observation_structure_material),
    )
    assert_state_answer_special_cases_contract(material)
    return material


def state_answer_special_cases_forward_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerSpecialCases):
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
        "enabled_case_ids",
        "source",
        "signal_summary",
        "self_denial",
        "anger",
        "gate_policy",
        "environment_state_output_frame",
        "human_follow_layer",
        "ratio_policy",
        "observation_structure_material",
        "surface_exception_policy",
        "selector_context",
        "state_answer_special_cases_connected",
        "state_answer_special_cases_material_only",
        "self_denial_special_handling_enabled",
        "anger_special_handling_enabled",
        "felt_state_is_real",
        "identity_claim_is_not_accepted",
        "emlis_impression_has_evidence",
        "limited_counter_opinion_allowed",
        "inner_value_line_receiving_allowed",
        "target_judgement_agreement_allowed",
        "target_attack_amplification_allowed",
        "identity_claim_as_fact_allowed",
        "blanket_personality_praise_allowed",
        "absolute_support_or_alliance_allowed",
        "over_comfort_allowed",
        "personality_claim_allowed",
        "completed_reply_generated",
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
        "gate_relaxed",
        "external_ai_used",
        "local_llm_used",
    }
    out = {key: copy.deepcopy(meta.get(key)) for key in keys if key in meta}
    assert_state_answer_special_cases_contract(out)
    return out


def state_answer_special_cases_gate_report(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerSpecialCases):
        return value.gate_report()
    meta = state_answer_special_cases_forward_meta(value)
    if not meta:
        return {}
    self_denial = _as_mapping(meta.get("self_denial"))
    anger = _as_mapping(meta.get("anger"))
    report = {
        "schema_version": meta.get("schema_version") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
        "material_id": meta.get("material_id") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
        "source_phase": meta.get("source_phase") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
        "passed": bool(meta.get("passed", True)),
        "evaluated": True,
        "status": meta.get("status") or "passed",
        "rejection_reasons": list(meta.get("rejection_reasons") or []),
        "enabled_case_ids": list(meta.get("enabled_case_ids") or []),
        "state_answer_special_cases_connected": True,
        "state_answer_special_cases_material_only": True,
        "self_denial_special_handling_enabled": bool(self_denial.get("enabled")),
        "anger_special_handling_enabled": bool(anger.get("enabled")),
        "felt_state_is_real": bool(self_denial.get("felt_state_is_real")),
        "identity_claim_is_not_accepted": bool(self_denial.get("identity_claim_is_not_accepted")),
        "emlis_impression_has_evidence": bool(self_denial.get("emlis_impression_has_evidence")),
        "limited_counter_opinion_allowed": bool(self_denial.get("limited_counter_opinion_allowed")),
        "self_denial_counter_opinion_requires_evidence": True,
        "self_denial_identity_claim_as_fact_allowed": False,
        "self_denial_personality_praise_allowed": False,
        "self_denial_absolute_support_allowed": False,
        "anger_target_judgement_agreement_blocked": True,
        "anger_target_attack_amplification_blocked": True,
        "anger_inner_value_line_receiving_allowed": bool(anger.get("inner_value_line_receiving_allowed")),
        "target_judgement_agreement_allowed": False,
        "target_attack_amplification_allowed": False,
        "personality_claim_allowed": False,
        "comment_text_generated": False,
        "raw_text_included": False,
        "display_gate_relaxed": False,
    }
    assert_state_answer_special_cases_contract(report)
    return report


def state_answer_special_cases_composer_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerSpecialCases):
        return value.composer_payload()
    meta = state_answer_special_cases_forward_meta(value)
    if not meta:
        return {}
    payload = {
        "schema_version": meta.get("schema_version") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
        "material_id": meta.get("material_id") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
        "source_phase": meta.get("source_phase") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
        "source": _deepcopy_mapping(_as_mapping(meta.get("source"))),
        "enabled_case_ids": list(meta.get("enabled_case_ids") or []),
        "self_denial": _deepcopy_mapping(_as_mapping(meta.get("self_denial"))),
        "anger": _deepcopy_mapping(_as_mapping(meta.get("anger"))),
        "gate_policy": _deepcopy_mapping(_as_mapping(meta.get("gate_policy"))),
        "state_answer_special_cases_connected": True,
        "state_answer_special_cases_material_only": True,
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_text_included": False,
        "display_gate_relaxed": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }
    assert_state_answer_special_cases_contract(payload)
    return payload


def state_answer_special_cases_surface_gate_check(
    visible_surface: Any = "",
    special_cases: Any = None,
    *,
    current_input: Any = None,
) -> dict[str, Any]:
    """Evaluate visible surface risk for Phase 5 special cases.

    ``visible_surface`` is used only in memory.  The returned dict is meta-only
    and does not include the candidate body or raw input.
    """

    meta = state_answer_special_cases_forward_meta(special_cases)
    if not meta and current_input is not None:
        meta = build_emlis_ai_state_answer_special_cases(current_input).as_meta()
    self_denial = _as_mapping(meta.get("self_denial"))
    anger = _as_mapping(meta.get("anger"))
    surface = _clean(visible_surface)

    self_denial_active = bool(self_denial.get("enabled"))
    anger_active = bool(anger.get("enabled"))
    safe_counter = bool(self_denial_active and _SELF_DENIAL_ALLOWED_COUNTER_RE.search(surface))
    self_denial_over_comfort = bool(self_denial_active and _SELF_DENIAL_FORBIDDEN_OVER_COMFORT_RE.search(surface))
    self_denial_identity_acceptance = bool(self_denial_active and _SELF_DENIAL_IDENTITY_ACCEPTANCE_RE.search(surface))
    anger_target_agreement = bool(anger_active and _ANGER_TARGET_JUDGEMENT_RE.search(surface))
    anger_attack = bool(anger_active and _ANGER_ATTACK_AMPLIFICATION_RE.search(surface))
    anger_inner_value_line = bool(anger_active and _ANGER_INNER_VALUE_LINE_RE.search(surface))

    rejection_reasons: list[str] = []
    warning_reasons: list[str] = []
    if self_denial_identity_acceptance:
        rejection_reasons.append("self_denial_identity_claim_accepted_as_fact")
    if self_denial_over_comfort:
        rejection_reasons.append("self_denial_over_comfort_or_personality_praise")
    if anger_target_agreement:
        rejection_reasons.append("anger_target_judgement_agreement")
    if anger_attack:
        rejection_reasons.append("anger_target_attack_amplification")
    if self_denial_active and not safe_counter and self_denial.get("limited_counter_opinion_allowed"):
        warning_reasons.append("self_denial_limited_counter_opinion_not_surface_detected")
    if anger_active and not anger_inner_value_line:
        warning_reasons.append("anger_inner_value_line_not_surface_detected")

    rejection_reasons = _dedupe(rejection_reasons)
    warning_reasons = _dedupe(warning_reasons)
    passed = not rejection_reasons
    report = {
        "schema_version": EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
        "material_id": EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
        "source_phase": EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
        "evaluated": True,
        "passed": bool(passed),
        "blocked": not bool(passed),
        "rejection_reasons": rejection_reasons,
        "surface_blocker_reasons": rejection_reasons,
        "warning_reasons": warning_reasons,
        "surface_warning_reasons": warning_reasons,
        "allowed_exception_ids_detected": _dedupe([
            "self_denial_limited_counter_opinion_as_emlis_impression" if safe_counter and not self_denial_over_comfort else "",
            "anger_inner_value_line_receiving" if anger_inner_value_line else "",
        ]),
        "state_answer_special_cases_connected": bool(meta),
        "self_denial_special_handling_enabled": self_denial_active,
        "anger_special_handling_enabled": anger_active,
        "self_denial_limited_counter_opinion_surface_allowed": bool(safe_counter and not self_denial_over_comfort),
        "self_denial_limited_counter_opinion_allowed": bool(safe_counter and not self_denial_over_comfort),
        "self_denial_exception_evidence_ready": bool(self_denial.get("emlis_impression_has_evidence")),
        "self_denial_over_comfort_or_personality_praise_detected": self_denial_over_comfort,
        "self_denial_identity_claim_accepted_as_fact_detected": self_denial_identity_acceptance,
        "anger_target_judgement_agreement_detected": anger_target_agreement,
        "anger_target_attack_amplification_detected": anger_attack,
        "anger_inner_value_line_receiving_detected": anger_inner_value_line,
        "target_judgement_agreement_allowed": False,
        "target_attack_amplification_allowed": False,
        "identity_claim_as_fact_allowed": False,
        "blanket_personality_praise_allowed": False,
        "absolute_support_or_alliance_allowed": False,
        "over_comfort_allowed": False,
        "personality_claim_allowed": False,
        "comment_text_generated": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "display_gate_relaxed": False,
        "gate_relaxed": False,
    }
    assert_state_answer_special_cases_contract(report, source="state_answer_special_cases_surface_gate_check")
    return report


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _FORBIDDEN_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_payload_key(child) for child in value)
    return False


def assert_state_answer_special_cases_contract(
    value: Any,
    *,
    source: str = "state_answer_special_cases",
) -> None:
    if isinstance(value, EmlisStateAnswerSpecialCases):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment surface payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    if _clean(value.get("schema_version")) not in {
        "",
        EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
    }:
        raise ValueError(f"{source} has unexpected schema_version")
    if _clean(value.get("material_id")) not in {"", EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID}:
        raise ValueError(f"{source} has unexpected material_id")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


# Project-local aliases for later connection phases.
build_state_answer_special_cases = build_emlis_ai_state_answer_special_cases
assert_emlis_state_answer_special_cases_contract = assert_state_answer_special_cases_contract

__all__ = [
    "EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION",
    "EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID",
    "EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE",
    "EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_INTERNAL_NAME",
    "EmlisStateAnswerSpecialCases",
    "build_emlis_ai_state_answer_special_cases",
    "build_state_answer_special_cases",
    "state_answer_special_cases_forward_meta",
    "state_answer_special_cases_gate_report",
    "state_answer_special_cases_composer_payload",
    "state_answer_special_cases_surface_gate_check",
    "assert_state_answer_special_cases_contract",
    "assert_emlis_state_answer_special_cases_contract",
]
