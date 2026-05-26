# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 bridge from the Emlis structure dictionary to Gate/Composer.

The Emlis observation structure dictionary is internal observation material.  It
must not become a public reply renderer, a fixed sentence template, or a source
of public contract drift.  This module therefore returns text-free material:
entry ids, relation ids, source-field names, evidence ids, and guard policies.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import copy
import json
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import EmlisCurrentInputBundle, build_emlis_current_input_bundle
from cocolon_environment_state_output_frame import (
    ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE,
    ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
    build_environment_state_output_frame,
)
from emlis_ai_state_answer_surface_contract import (
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
    assert_emlis_state_answer_surface_contract,
    build_emlis_state_answer_surface_contract,
    state_answer_surface_contract_composer_payload,
    state_answer_surface_contract_forward_meta,
    state_answer_surface_contract_gate_report,
)
from emlis_ai_observation_structure_dictionary_loader import (
    OBSERVATION_STRUCTURE_DICTIONARY_BASE,
    OBSERVATION_STRUCTURE_DICTIONARY_ID,
    OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE,
    OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION,
    ObservationStructureDictionary,
    ObservationStructureEntry,
    ObservationStructureRelation,
    load_observation_structure_dictionary,
)

OBSERVATION_STRUCTURE_MATERIAL_SCHEMA_VERSION: Final = "emlis.observation_structure_material.v1"
OBSERVATION_STRUCTURE_MATERIAL_PHASE: Final = "Phase4_Gate_Composer_Connection"

_SPACE_RE: Final = re.compile(r"\s+")
_PUNCT_RE: Final = re.compile(r"[\s\u3000。．、，,.!！?？:：;；\-ー_\/\\]+")
_GAP_WORD_RE: Final = re.compile(r"(大丈夫|平気|なんでもない|何でもない|大したことない|大丈夫なはず|まあいいか)")
_STATE_WEIGHT_WORD_RE: Final = re.compile(r"(無理|もう無理|限界|しんどい|疲れた|消耗|怖い|こわい|不安|嫌だ|いやだ)")
_DISCREPANCY_RE: Final = re.compile(
    r"(本当は|ほんとは|内心|心では|嫌だった|いやだった|笑って対応|我慢|隠し|隠す|耐え|言えなかった|合わせた|平気なふり|大丈夫なふり)"
)
_WORK_HEALTH_OVERLAP_RE: Final = re.compile(r"(残業|眠れ|眠れて|体|身体|体調|健康|持たない|疲労|休め|仕事の負荷)")
_WORK_RELATION_OVERLAP_RE: Final = re.compile(r"(上司|同僚|部下|職場|人との|関わり|人間関係|相手|追加.*頼まれ|対応した)")
_TEXTUAL_TARGET_RE: Final = re.compile(r"(明日|今日|予定|仕事|職場|学校|人間関係|相手|家族|体|身体|健康|生活|環境|状況|自分)")
_UNEXPRESSED_OUTPUT_STOP_RE: Final = re.compile(r"(言えなかった|言えない|伝えられなかった|飲み込んだ|言葉にできなかった)")
_SELF_SHAPE_ALIGNMENT_RE: Final = re.compile(r"(合わせた|合わせてしまった|空気を読んだ|場に合わせた|相手に合わせた)")
_ACTION_CONVERSION_HISTORY_RE: Final = re.compile(r"(我慢した|我慢してる|我慢していた|耐えた|抑えた|言わずにいた)")
_CONVERSION_HISTORY_CLOSURE_RE: Final = re.compile(r"(納得|まだ|引っかか|ひっかか|仕方ない|また|疲れた|将来|未来|関係|意味が返ってこない)")
_UNFORMED_SELF_INSIGHT_RE: Final = re.compile(r"(わからない|分からない|どうしたらいいかわからない|どうしたらいいか分からない|何が嫌なのかわからない|何が嫌なのか分からない|なんでこうなるんだろう|しっくりこない|違和感がある)")
_PRIORITY_PRESSURE_EVIDENCE_RE: Final = re.compile(r"(優先|圧力|プレッシャ|求められ|強要|言われ|断れな|空気を読まないと|合わせなきゃ|合わせないと|期待|急に|頼まれ)")
_LOAD_OR_FATIGUE_EVIDENCE_RE: Final = re.compile(r"(疲れ|疲労|消耗|負荷|重い|何度も|繰り返|また|続い|耐え続け|我慢し続け)")

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
        "thought_text",
        "action_text",
        "comment_text",
        "commentText",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "completed_reply_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "comment_text_generated",
        "public_status_extended",
        "observation_status_enum_extended",
        "api_response_key_change",
        "response_key_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "reader_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "completed_sentence_template_used",
        "dictionary_returns_completed_reply",
        "dictionary_returned_completed_reply",
        "completed_reply_from_dictionary",
        "external_ai_used",
        "local_llm_used",
        "cause_created_from_category",
        "cause_created_from_emotion_strength",
        "cause_inferred_from_category",
        "cause_inferred_from_emotion_strength",
        "personality_inference_allowed",
        "personality_tendency_allowed",
        "period_tendency_from_single_record",
        "period_tendency_allowed",
        "recovery_prescription_allowed",
        "recovery_prescription",
        "cause_from_category",
        "cause_from_emotion_strength",
        "public_payload_changed",
        "public_response_key_added",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = [values]
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _FORBIDDEN_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


def _compact_len(value: str) -> int:
    return len(_PUNCT_RE.sub("", value or ""))


def _bundle_text(bundle: EmlisCurrentInputBundle) -> str:
    # Internal-only matching string. It is never returned by this module.
    return _clean("。".join(part for part in (bundle.thought_text, bundle.action_text) if _clean(part)))


def _emotion_types(bundle: EmlisCurrentInputBundle) -> list[str]:
    return _dedupe(emotion.type for emotion in bundle.emotions)


def _emotion_strengths(bundle: EmlisCurrentInputBundle) -> list[str]:
    return _dedupe(emotion.strength for emotion in bundle.emotions if emotion.strength)


def _source_fields_for_entry(entry: ObservationStructureEntry, *, bundle: EmlisCurrentInputBundle) -> list[str]:
    fields: list[str] = []
    emotion_set = set(_emotion_types(bundle))
    for word in entry.input_words:
        word_text = _clean(word)
        if not word_text:
            continue
        if bundle.thought_text and word_text in bundle.thought_text:
            fields.append("memo")
        if bundle.action_text and word_text in bundle.action_text:
            fields.append("memo_action")
        if word_text in emotion_set:
            fields.append("emotion_details")
    if entry.entry_type == "emotion_relation" and len(bundle.emotions) >= 2:
        fields.append("emotion_details")
    if entry.entry_type == "special_emotion_mode" and "自己理解" in emotion_set:
        fields.append("emotion_details")
    if entry.entry_type == "thought_action_relation" and bundle.thought_text and bundle.action_text:
        fields.extend(["memo", "memo_action"])
    if entry.entry_type == "category_relation" and len(bundle.categories) >= 2:
        fields.append("category")
    if entry.entry_type == "prompt_policy":
        fields.extend(["memo", "emotion_details", "category"])
    return _dedupe(fields)


def _has_gap_word(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_GAP_WORD_RE.search(_bundle_text(bundle)))


def _has_state_weight_word(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_STATE_WEIGHT_WORD_RE.search(_bundle_text(bundle)))


def _has_textual_target(bundle: EmlisCurrentInputBundle) -> bool:
    # Category labels are not causes; this only reads explicit memo/action text.
    return bool(_TEXTUAL_TARGET_RE.search(_bundle_text(bundle)))


def _has_thought_action_discrepancy(bundle: EmlisCurrentInputBundle) -> bool:
    if not bundle.thought_text or not bundle.action_text:
        return False
    joined = _bundle_text(bundle)
    if _DISCREPANCY_RE.search(joined):
        return True
    return bool(_GAP_WORD_RE.search(bundle.thought_text) and _DISCREPANCY_RE.search(bundle.action_text))


def _has_unexpressed_output_stop(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_UNEXPRESSED_OUTPUT_STOP_RE.search(_bundle_text(bundle)))


def _has_self_shape_alignment(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_SELF_SHAPE_ALIGNMENT_RE.search(_bundle_text(bundle)))


def _has_action_conversion_history(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_ACTION_CONVERSION_HISTORY_RE.search(_bundle_text(bundle)))


def _has_conversion_history_closure_evidence(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_has_action_conversion_history(bundle) and _CONVERSION_HISTORY_CLOSURE_RE.search(_bundle_text(bundle)))


def _has_unformed_self_insight(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_UNFORMED_SELF_INSIGHT_RE.search(_bundle_text(bundle)))


def _has_priority_pressure_evidence(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_PRIORITY_PRESSURE_EVIDENCE_RE.search(_bundle_text(bundle)))


def _has_load_or_fatigue_evidence(bundle: EmlisCurrentInputBundle) -> bool:
    return bool(_LOAD_OR_FATIGUE_EVIDENCE_RE.search(_bundle_text(bundle)))


def _filter_relation_ids_by_evidence(
    relation_ids: Sequence[str],
    *,
    bundle: EmlisCurrentInputBundle,
    low_information_candidate: bool,
) -> list[str]:
    """Promote dictionary relation candidates only with current-input evidence."""

    out: list[str] = []
    for relation_id in relation_ids:
        relation_id = _clean(relation_id)
        if relation_id == "unexpressed_output_stop" and not _has_unexpressed_output_stop(bundle):
            continue
        if relation_id == "self_shape_alignment" and not _has_self_shape_alignment(bundle):
            continue
        if relation_id == "action_conversion_history" and not _has_action_conversion_history(bundle):
            continue
        if relation_id == "unformed_self_insight" and not _has_unformed_self_insight(bundle):
            continue
        if relation_id == "thought_action_discrepancy" and not _has_thought_action_discrepancy(bundle):
            continue
        if relation_id == "conversion_history_closure" and not _has_conversion_history_closure_evidence(bundle):
            continue
        if relation_id == "priority_pressure" and not _has_priority_pressure_evidence(bundle):
            continue
        if relation_id == "load_accumulation" and not _has_load_or_fatigue_evidence(bundle):
            continue
        if relation_id in {"low_information_weight", "user_agency_prompt"} and not low_information_candidate:
            continue
        out.append(relation_id)
    return _dedupe(out)


def _has_category_overlap(bundle: EmlisCurrentInputBundle) -> bool:
    categories = set(bundle.categories)
    joined = _bundle_text(bundle)
    if not joined or len(categories) < 2:
        return False
    if {"仕事", "健康"}.issubset(categories) and _WORK_HEALTH_OVERLAP_RE.search(joined):
        return True
    if {"仕事", "人間関係"}.issubset(categories) and _WORK_RELATION_OVERLAP_RE.search(joined):
        return True
    return False


def _is_low_information_candidate(bundle: EmlisCurrentInputBundle) -> bool:
    text = _bundle_text(bundle)
    if not text:
        return True
    compact_text = _PUNCT_RE.sub("", text or "")
    compact = len(compact_text)
    no_action = not bool(bundle.action_text)
    low_info_exact = {"無理", "もう無理", "しんどい", "限界", "疲れた", "大丈夫", "平気", "なんでもない", "何でもない"}
    if no_action and compact_text in low_info_exact:
        return True
    if no_action and _has_gap_word(bundle) and compact <= 10:
        return True
    if no_action and compact <= 10 and _has_state_weight_word(bundle) and not _has_textual_target(bundle):
        return True
    # Targeted short expressions such as "明日が怖い" have a visible target and
    # should remain eligible for the existing current-input router.  Do not let
    # dictionary-only low-information material downgrade them.
    return False


def _relation_ids_from_graph(observation_graph: Any) -> list[str]:
    relation_ids: list[str] = []
    candidates: list[Any] = []
    if isinstance(observation_graph, Mapping):
        for key in ("edges", "relations", "relation_edges", "core_tensions"):
            value = observation_graph.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                candidates.extend(value)
    else:
        for attr in ("edges", "relations", "relation_edges", "core_tensions"):
            value = getattr(observation_graph, attr, None)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                candidates.extend(value)
    for item in candidates:
        if isinstance(item, Mapping):
            relation_ids.append(_clean(item.get("relation_type") or item.get("relation_id") or item.get("type")))
        else:
            relation_ids.append(_clean(getattr(item, "relation_type", None) or getattr(item, "relation_id", None) or getattr(item, "type", None)))
    return _dedupe(relation_ids)


def _span_id(span: Any, index: int) -> str:
    if isinstance(span, Mapping):
        return _clean(span.get("span_id") or span.get("id") or span.get("ref_id") or f"s{index + 1}")
    return _clean(getattr(span, "span_id", None) or getattr(span, "id", None) or getattr(span, "ref_id", None) or f"s{index + 1}")


def _span_source(span: Any) -> str:
    if isinstance(span, Mapping):
        return _clean(span.get("source_field"))
    return _clean(getattr(span, "source_field", ""))


def _evidence_ids_for_fields(evidence_ledger: Any, fields: Sequence[str]) -> list[str]:
    if not isinstance(evidence_ledger, Sequence) or isinstance(evidence_ledger, (str, bytes, bytearray)):
        return []
    wanted = set(fields)
    out: list[str] = []
    for index, span in enumerate(evidence_ledger):
        if _span_source(span) in wanted:
            out.append(_span_id(span, index))
    return _dedupe(out)


def _axis_source_fields(frame: Mapping[str, Any]) -> list[str]:
    fields: list[str] = []
    environment_axis = frame.get("environment_axis") or {}
    state_axis = frame.get("state_axis") or {}
    output_axis = frame.get("output_axis") or {}
    if environment_axis.get("category_labels"):
        fields.append("category")
    if (environment_axis.get("action_evidence") or {}).get("has_action_text"):
        fields.append("memo_action")
    if state_axis.get("emotion_labels"):
        fields.append("emotion_details")
    if (output_axis.get("thought_evidence") or {}).get("has_thought_text"):
        fields.append("memo")
    return _dedupe(fields)


def _environment_state_output_frame_material_projection(frame: Mapping[str, Any]) -> dict[str, Any]:
    """Return a Phase4-safe projection of the Phase3 frame.

    The full Phase3 builder output stays internal.  Phase4 forwards only
    Gate/Composer-useful structure: axes, selected labels, ids, evidence ids,
    confidence kinds, and closed policy flags.  It does not forward raw
    memo/memo_action text, completed replies, public text, or the direct
    ``surface_policy`` object from the builder.
    """

    environment_axis = dict(frame.get("environment_axis") or {})
    state_axis = dict(frame.get("state_axis") or {})
    output_axis = dict(frame.get("output_axis") or {})
    time_axis = dict(frame.get("time_axis") or {})
    evidence = dict(frame.get("evidence") or {})
    frame_policy = dict(frame.get("surface_policy") or {})
    source = dict(frame.get("source") or {})
    bridge = dict(frame.get("observation_structure_bridge") or {})

    category_labels = [
        _clean(item.get("label"))
        for item in environment_axis.get("category_labels") or []
        if isinstance(item, Mapping) and _clean(item.get("label"))
    ]
    emotion_types = [
        _clean(item.get("type"))
        for item in state_axis.get("emotion_labels") or []
        if isinstance(item, Mapping) and _clean(item.get("type"))
    ]
    state_gap_candidate_ids = [
        _clean(item.get("candidate_id"))
        for item in state_axis.get("state_text_gap_candidates") or []
        if isinstance(item, Mapping) and _clean(item.get("candidate_id"))
    ]
    output_theme_ids = [
        _clean(item.get("theme_id"))
        for item in output_axis.get("output_theme_candidates") or []
        if isinstance(item, Mapping) and _clean(item.get("theme_id"))
    ]
    output_theme_candidates: list[dict[str, Any]] = []
    for item in output_axis.get("output_theme_candidates") or []:
        if not isinstance(item, Mapping):
            continue
        theme_id = _clean(item.get("theme_id"))
        if not theme_id:
            continue
        output_theme_candidates.append(
            {
                "theme_id": theme_id,
                "evidence_span_ids": _dedupe(item.get("evidence_span_ids") or []),
                "confidence_kind": _clean(item.get("confidence_kind")) or "explicit_text_evidence",
                "allowed_surface_strength": _clean(item.get("allowed_surface_strength")) or "soft",
                "read_as": "current_output_theme_candidate",
                "must_not_read_as": ["personality_tendency", "period_tendency", "diagnosis", "cause"],
                "raw_input_included": False,
                "raw_text_included": False,
                "comment_text_generated": False,
                "completed_reply_generated": False,
            }
        )
    evidence_span_ids = [
        _clean(item.get("span_id"))
        for item in evidence.get("spans") or []
        if isinstance(item, Mapping) and _clean(item.get("span_id"))
    ]
    source_fields = _axis_source_fields(frame)

    return {
        "schema_version": frame.get("schema_version") or ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
        "material_id": frame.get("material_id") or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
        "phase": frame.get("phase") or ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE,
        "projection_kind": "phase4_gate_composer_safe_projection",
        "source": {
            "source_kind": source.get("source_kind") or "current_input",
            "selected_at_present": bool(source.get("selected_at")),
            "source_record_id_present": bool(source.get("source_record_id")),
            "bundle_schema_version": source.get("bundle_schema_version") or "",
        },
        "axis_presence": copy.deepcopy(dict(frame.get("axis_presence") or {})),
        "environment_axis": {
            "source_fields": [field for field in ("category", "memo_action") if field in source_fields],
            "category_labels": _dedupe(category_labels),
            "category_count": len(_dedupe(category_labels)),
            "has_action_text": bool((environment_axis.get("action_evidence") or {}).get("has_action_text")),
            "confidence_kind": environment_axis.get("confidence_kind") or "environment_axis_missing",
            "read_as": "topic_direction_plus_action_evidence",
            "must_not_read_as": ["cause"],
        },
        "state_axis": {
            "source_fields": ["emotion_details"] if "emotion_details" in source_fields else [],
            "emotion_types": _dedupe(emotion_types),
            "emotion_count": len(_dedupe(emotion_types)),
            "strength_summary": copy.deepcopy(dict(state_axis.get("strength_summary") or {})),
            "state_text_gap_candidate_ids": _dedupe(state_gap_candidate_ids),
            "confidence_kind": state_axis.get("confidence_kind") or "state_axis_missing",
            "read_as": "state_label",
            "must_not_read_as": ["diagnosis", "cause"],
        },
        "output_axis": {
            "source_fields": ["memo"] if "memo" in source_fields else [],
            "has_thought_text": bool((output_axis.get("thought_evidence") or {}).get("has_thought_text")),
            "output_theme_ids": _dedupe(output_theme_ids),
            "output_theme_candidates": output_theme_candidates,
            "output_theme_count": len(_dedupe(output_theme_ids)),
            "confidence_kind": output_axis.get("confidence_kind") or "output_axis_missing",
            "read_as": "output_content",
            "must_not_read_as": ["personality_tendency", "period_tendency", "diagnosis"],
        },
        "time_axis": {
            "period_scope": time_axis.get("period_scope") or "single_record",
            "must_not_use_for_period_tendency": True,
        },
        "observation_structure_bridge": {
            "selected_relation_ids": _dedupe(bridge.get("selected_relation_ids") or []),
            "relation_ids_are_candidates_only": bool(bridge.get("relation_ids_are_candidates_only", True)),
            "bridge_used_for_surface_text": False,
        },
        "evidence": {
            "evidence_span_ids": _dedupe(evidence_span_ids),
            "span_count": len(_dedupe(evidence_span_ids)),
            "raw_text_included": False,
            "redacted_preview_included": False,
        },
        "frame_policy": {
            "single_record_only": True,
            "must_use_scope_marker": bool(frame_policy.get("must_use_scope_marker", True)),
            "scope_marker": frame_policy.get("scope_marker") or "今回の入力では",
            "forbidden_claims": _dedupe(frame_policy.get("forbidden_claims") or []),
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "public_payload_changed": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
            "personality_tendency_allowed": False,
            "recovery_prescription_allowed": False,
        },
    }


def _build_environment_state_output_frame_projection(current_input: Any, relation_ids: Sequence[str]) -> dict[str, Any]:
    frame = build_environment_state_output_frame(
        current_input,
        observation_structure_relation_ids=list(relation_ids),
    )
    return _environment_state_output_frame_material_projection(frame)


def _relation_policy_ids(relation_ids: Sequence[str]) -> list[str]:
    out: list[str] = []
    for relation_id in relation_ids:
        if relation_id in {"state_text_gap", "emotion_nesting", "thought_action_discrepancy", "category_parallel", "category_overlap"}:
            out.append("state_language")
        if relation_id in {"low_information_weight", "user_agency_prompt"}:
            out.append("low_information_boundary")
        if relation_id in {"desire_stagnation", "load_accumulation", "action_blocked", "pressure_gap", "repetition", "priority_pressure"}:
            out.append("relation_candidate")
        if relation_id == "self_insight_discovery":
            out.append("self_insight_mode")
    return _dedupe(out)


def _question_ids(entry: ObservationStructureEntry) -> list[str]:
    return [f"{entry.entry_id}:q{index + 1}" for index, _question in enumerate(entry.observation_questions)]


def _forbidden_count(entries: Sequence[ObservationStructureEntry], relations: Sequence[ObservationStructureRelation]) -> int:
    total = 0
    for relation in relations:
        total += len(relation.forbidden_inference or ())
    for entry in entries:
        total += len(entry.forbidden_inference or ())
        for question in entry.observation_questions or ():
            total += len(question.forbidden_inference or ())
    return total


def _selected_entries_for_bundle(
    dictionary: ObservationStructureDictionary,
    *,
    bundle: EmlisCurrentInputBundle,
) -> list[ObservationStructureEntry]:
    text_for_match = _bundle_text(bundle)
    emotion_set = set(_emotion_types(bundle))
    selected: list[ObservationStructureEntry] = []
    for entry in dictionary.entries:
        entry_type = _clean(entry.entry_type)
        matched = False
        if entry_type == "special_emotion_mode" and any(word in emotion_set for word in entry.input_words):
            matched = True
        elif entry_type == "emotion_relation" and len(bundle.emotions) >= 2:
            matched = True
        elif entry_type == "thought_action_relation" and _has_thought_action_discrepancy(bundle):
            matched = True
        elif entry_type == "category_relation" and len(bundle.categories) >= 2:
            matched = True
        elif entry_type == "prompt_policy" and _is_low_information_candidate(bundle):
            matched = True
        else:
            matched = any(_clean(word) and _clean(word) in text_for_match for word in entry.input_words)
        if matched:
            selected.append(entry)
    return selected


@dataclass(frozen=True)
class ObservationStructureMaterial:
    """Text-free Phase 4 material passed to Gate and Composer."""

    dictionary_id: str
    dictionary_version: str
    dictionary_schema_version: str
    base_dictionary: str
    loader_phase: str
    selected_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    selected_entry_types: tuple[str, ...] = field(default_factory=tuple)
    selected_relation_ids: tuple[str, ...] = field(default_factory=tuple)
    graph_relation_ids: tuple[str, ...] = field(default_factory=tuple)
    structure_question_ids: tuple[str, ...] = field(default_factory=tuple)
    matched_source_fields: tuple[str, ...] = field(default_factory=tuple)
    relation_policy_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_span_ids: tuple[str, ...] = field(default_factory=tuple)
    bundle_field_flags: Mapping[str, Any] = field(default_factory=dict)
    gate_policy: Mapping[str, Any] = field(default_factory=dict)
    composer_policy: Mapping[str, Any] = field(default_factory=dict)
    contract_safety: Mapping[str, Any] = field(default_factory=dict)
    environment_state_output_frame: Mapping[str, Any] = field(default_factory=dict)
    state_answer_surface_contract: Mapping[str, Any] = field(default_factory=dict)
    forbidden_inference_count: int = 0
    low_information_candidate: bool = False
    passed: bool = True
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = OBSERVATION_STRUCTURE_MATERIAL_SCHEMA_VERSION
    source_phase: str = OBSERVATION_STRUCTURE_MATERIAL_PHASE

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "version": self.schema_version,
            "source_phase": self.source_phase,
            "source_step": self.source_phase,
            "phase": self.source_phase,
            "dictionary_id": self.dictionary_id,
            "dictionary_version": self.dictionary_version,
            "dictionary_schema_version": self.dictionary_schema_version,
            "base_dictionary": self.base_dictionary,
            "loader_phase": self.loader_phase,
            "passed": bool(self.passed),
            "evaluated": True,
            "status": "passed" if self.passed else "rejected",
            "rejection_reasons": list(self.rejection_reasons),
            "selected_entry_ids": list(self.selected_entry_ids),
            "matched_entry_ids": list(self.selected_entry_ids),
            "selected_entry_types": list(self.selected_entry_types),
            "selected_relation_ids": list(self.selected_relation_ids),
            "structure_relation_ids": list(self.selected_relation_ids),
            "graph_relation_ids": list(self.graph_relation_ids),
            "structure_question_ids": list(self.structure_question_ids),
            "constraint_ids": list(self.relation_policy_ids),
            "matched_source_fields": list(self.matched_source_fields),
            "relation_policy_ids": list(self.relation_policy_ids),
            "evidence_span_ids": list(self.evidence_span_ids),
            "bundle_field_flags": copy.deepcopy(dict(self.bundle_field_flags)),
            "gate_policy": copy.deepcopy(dict(self.gate_policy)),
            "composer_policy": copy.deepcopy(dict(self.composer_policy)),
            "contract_safety": copy.deepcopy(dict(self.contract_safety)),
            "environment_state_output_frame": copy.deepcopy(dict(self.environment_state_output_frame or {})),
            "environment_state_output_frame_connected": bool(self.environment_state_output_frame),
            "environment_state_output_frame_material_id": (self.environment_state_output_frame or {}).get("material_id") or "",
            "environment_state_output_frame_schema_version": (self.environment_state_output_frame or {}).get("schema_version") or "",
            "environment_state_output_frame_phase": (self.environment_state_output_frame or {}).get("phase") or "",
            "environment_state_output_frame_single_record_only": bool(((self.environment_state_output_frame or {}).get("frame_policy") or {}).get("single_record_only")),
            "environment_state_output_frame_safe_projection": bool(self.environment_state_output_frame),
            "state_answer_surface_contract": copy.deepcopy(dict(self.state_answer_surface_contract or {})),
            "state_answer_surface_contract_connected": bool(self.state_answer_surface_contract),
            "state_answer_surface_contract_material_id": (self.state_answer_surface_contract or {}).get("material_id") or "",
            "state_answer_surface_contract_schema_version": (self.state_answer_surface_contract or {}).get("schema_version") or "",
            "state_answer_surface_contract_phase": (self.state_answer_surface_contract or {}).get("phase") or (self.state_answer_surface_contract or {}).get("source_phase") or "",
            "state_answer_surface_contract_observation_layer_connected": bool((self.state_answer_surface_contract or {}).get("observation_layer")),
            "state_answer_surface_contract_human_follow_layer_connected": bool((self.state_answer_surface_contract or {}).get("human_follow_layer")),
            "state_answer_surface_contract_material_only": bool(self.state_answer_surface_contract),
            "forbidden_inference_count": int(self.forbidden_inference_count),
            "low_information_candidate": bool(self.low_information_candidate),
            "period_tendency_from_single_record": False,
            "recovery_prescription_allowed": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "structure_dictionary_loaded": True,
            "observation_structure_dictionary_connected": True,
            "structure_dictionary_material_ready": True,
            "input_bundle_policy_connected": True,
            "phase4_gate_composer_connection_ready": True,
            "gate_connection_ready": True,
            "composer_connection_ready": True,
            "gate_connected": True,
            "composer_connected": True,
            "dictionary_returns_completed_reply": False,
            "dictionary_returned_completed_reply": False,
            "completed_reply_from_dictionary": False,
            "dictionary_is_completed_reply_template": False,
            "dictionary_is_observation_material_only": True,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "fixed_sentence_template_used": False,
            "completed_sentence_template_used": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "api_response_key_change": False,
            "request_key_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "cause_inferred_from_category": False,
            "cause_inferred_from_emotion_strength": False,
            "personality_tendency_allowed": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_observation_structure_material_contract(meta)
        return meta

    def gate_report(self) -> dict[str, Any]:
        meta = self.as_meta()
        return {
            "passed": meta["passed"],
            "evaluated": True,
            "status": meta["status"],
            "rejection_reasons": meta["rejection_reasons"],
            "selected_entry_ids": meta["selected_entry_ids"],
            "selected_relation_ids": meta["selected_relation_ids"],
            "constraint_ids": meta["constraint_ids"],
            "dictionary_material_only": True,
            "dictionary_returns_completed_reply": False,
            "dictionary_returned_completed_reply": False,
            "completed_reply_from_dictionary": False,
            "display_gate_relaxed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "cause_inferred_from_category": False,
            "cause_inferred_from_emotion_strength": False,
            "personality_tendency_allowed": False,
            "period_tendency_from_single_record": False,
            "recovery_prescription_allowed": False,
            "environment_state_output_frame_connected": bool(self.environment_state_output_frame),
            "environment_state_output_frame_material_id": (self.environment_state_output_frame or {}).get("material_id") or "",
            "environment_state_output_frame_axis_presence": copy.deepcopy(dict((self.environment_state_output_frame or {}).get("axis_presence") or {})),
            "environment_state_output_frame_output_theme_ids": list(((self.environment_state_output_frame or {}).get("output_axis") or {}).get("output_theme_ids") or []),
            "state_answer_surface_contract_connected": bool(self.state_answer_surface_contract),
            "state_answer_surface_contract_material_id": (self.state_answer_surface_contract or {}).get("material_id") or "",
            "state_answer_surface_contract_gate_report": state_answer_surface_contract_gate_report(self.state_answer_surface_contract) if self.state_answer_surface_contract else {},
        }

    def composer_payload(self) -> dict[str, Any]:
        meta = self.as_meta()
        return {
            "schema_version": meta["schema_version"],
            "source_phase": meta["source_phase"],
            "dictionary_id": meta["dictionary_id"],
            "dictionary_version": meta["dictionary_version"],
            "base_dictionary": meta["base_dictionary"],
            "selected_entry_ids": meta["selected_entry_ids"],
            "selected_relation_ids": meta["selected_relation_ids"],
            "structure_question_ids": meta["structure_question_ids"],
            "matched_source_fields": meta["matched_source_fields"],
            "relation_policy_ids": meta["relation_policy_ids"],
            "evidence_span_ids": meta["evidence_span_ids"],
            "bundle_field_flags": meta["bundle_field_flags"],
            "gate_policy": meta["gate_policy"],
            "composer_policy": meta["composer_policy"],
            "forbidden_inference_count": meta["forbidden_inference_count"],
            "low_information_candidate": meta["low_information_candidate"],
            "environment_state_output_frame": copy.deepcopy(dict(meta.get("environment_state_output_frame") or {})),
            "environment_state_output_frame_connected": bool(meta.get("environment_state_output_frame_connected")),
            "environment_state_output_frame_material_id": meta.get("environment_state_output_frame_material_id") or "",
            "environment_state_output_frame_schema_version": meta.get("environment_state_output_frame_schema_version") or "",
            "environment_state_output_frame_single_record_only": bool(meta.get("environment_state_output_frame_single_record_only")),
            "state_answer_surface_contract": state_answer_surface_contract_composer_payload(meta.get("state_answer_surface_contract") or {}) if meta.get("state_answer_surface_contract") else {},
            "state_answer_surface_contract_connected": bool(meta.get("state_answer_surface_contract_connected")),
            "state_answer_surface_contract_material_id": meta.get("state_answer_surface_contract_material_id") or "",
            "state_answer_surface_contract_schema_version": meta.get("state_answer_surface_contract_schema_version") or "",
            "period_tendency_from_single_record": False,
            "recovery_prescription_allowed": False,
            "dictionary_is_observation_material_only": True,
            "dictionary_returns_completed_reply": False,
            "dictionary_returned_completed_reply": False,
            "completed_reply_from_dictionary": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "cause_inferred_from_category": False,
            "cause_inferred_from_emotion_strength": False,
            "personality_tendency_allowed": False,
        }


def _bundle_field_flags(bundle: EmlisCurrentInputBundle) -> dict[str, Any]:
    summary = bundle.emotion_strength_summary.to_dict()
    return {
        "has_memo_field": bool(bundle.thought_text),
        "has_memo_action_field": bool(bundle.action_text),
        "has_emotion_details_field": bool(bundle.emotions),
        "has_category_field": bool(bundle.categories),
        "emotion_count": len(bundle.emotions),
        "category_count": len(bundle.categories),
        "has_multiple_emotions": len(bundle.emotions) >= 2,
        "has_multiple_categories": len(bundle.categories) >= 2,
        "has_strong_emotion": bool(summary.get("has_strong")),
        "primary_emotion_type": _clean(summary.get("primary_type")),
        "primary_emotion_strength": _clean(summary.get("primary_strength")),
        "strongest_emotion_type": _clean(summary.get("strongest_type")),
        "strongest_emotion_strength": _clean(summary.get("strongest_strength")),
        "selected_emotion_types": _emotion_types(bundle),
        "selected_strengths": _emotion_strengths(bundle),
        "selected_at_present": bool(bundle.selected_at),
        "source_record_id_present": bool(bundle.source_record_id),
    }


def _dictionary(value: ObservationStructureDictionary | None = None) -> ObservationStructureDictionary:
    return value if isinstance(value, ObservationStructureDictionary) else load_observation_structure_dictionary()


def build_observation_structure_material(
    *,
    current_input: Any,
    dictionary: ObservationStructureDictionary | None = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
) -> ObservationStructureMaterial:
    """Build text-free observation structure material for Gate/Composer."""

    bundle = build_emlis_current_input_bundle(current_input)
    structure_dictionary = _dictionary(dictionary)
    relation_lookup = {relation.relation_id: relation for relation in structure_dictionary.relations}

    selected_entries = _selected_entries_for_bundle(structure_dictionary, bundle=bundle)
    low_information_candidate = _is_low_information_candidate(bundle)
    selected_relation_ids: list[str] = []
    source_fields: list[str] = []
    question_ids: list[str] = []

    for entry in selected_entries:
        selected_relation_ids.extend(
            _filter_relation_ids_by_evidence(
                entry.relation_candidates,
                bundle=bundle,
                low_information_candidate=low_information_candidate,
            )
        )
        source_fields.extend(_source_fields_for_entry(entry, bundle=bundle))
        question_ids.extend(_question_ids(entry))

    if _has_gap_word(bundle) and bundle.emotions:
        selected_relation_ids.append("state_text_gap")
        source_fields.extend(["memo", "memo_action", "emotion_details", "category"])
    if len(bundle.emotions) >= 2:
        selected_relation_ids.append("emotion_nesting")
        source_fields.append("emotion_details")
    if len(bundle.categories) >= 2:
        selected_relation_ids.append("category_parallel")
        source_fields.append("category")
    if _has_category_overlap(bundle):
        selected_relation_ids.append("category_overlap")
        source_fields.extend(["memo", "memo_action", "category"])
    elif "category_overlap" in selected_relation_ids:
        # A category relation entry carries both candidates.  Without input-text
        # evidence, keep only the parallel relation to avoid causal overclaim.
        selected_relation_ids = [item for item in selected_relation_ids if item != "category_overlap"]
    if _has_thought_action_discrepancy(bundle):
        selected_relation_ids.append("thought_action_discrepancy")
        source_fields.extend(["memo", "memo_action"])
    if "自己理解" in _emotion_types(bundle):
        selected_relation_ids.append("self_insight_discovery")
        source_fields.append("emotion_details")

    if low_information_candidate:
        selected_relation_ids.extend(["low_information_weight", "user_agency_prompt"])
        source_fields.extend(["memo", "emotion_details", "category"])
    selected_relation_ids = _filter_relation_ids_by_evidence(
        selected_relation_ids,
        bundle=bundle,
        low_information_candidate=low_information_candidate,
    )

    graph_relation_ids = [item for item in _relation_ids_from_graph(observation_graph) if item in relation_lookup]
    selected_relation_ids.extend(graph_relation_ids)
    selected_relation_ids = [item for item in _dedupe(selected_relation_ids) if item in relation_lookup]
    selected_relations = [relation_lookup[item] for item in selected_relation_ids]

    selected_entry_ids = _dedupe(entry.entry_id for entry in selected_entries)
    selected_entry_types = _dedupe(entry.entry_type for entry in selected_entries)
    matched_source_fields = _dedupe(source_fields)

    gate_policy = {
        "low_information_boundary_connected": True,
        "overclaim_guard_connected": True,
        "forbidden_inference_boundary_connected": True,
        "category_is_topic_direction_not_cause": True,
        "category_overlap_requires_textual_evidence": True,
        "emotion_strength_affects_state_weight_only": True,
        "emotion_strength_must_not_create_cause": True,
        "memo_is_self_world_event": True,
        "memo_action_is_real_world_event": True,
        "source_priority_preserved": True,
        "dictionary_candidates_lower_than_current_explicit_fields": True,
        "must_not_promote_low_information_from_dictionary_only": True,
        "environment_state_output_frame_connected": True,
        "environment_state_output_frame_is_single_record": True,
        "period_tendency_from_single_record": False,
        "recovery_prescription_allowed": False,
    }
    composer_policy = {
        "observation_material_only": True,
        "dictionary_must_not_return_completed_sentence": True,
        "use_for_input_organization": True,
        "use_for_relation_candidates": True,
        "use_for_internal_question_ids": True,
        "use_for_user_agency_prompt_policy": True,
        "surface_realizer_owns_natural_language": True,
        "must_not_create_cause_without_evidence": True,
        "must_not_personality_diagnose": True,
        "must_not_use_fixed_reply_template": True,
        "environment_state_output_frame_available": True,
        "environment_state_output_frame_is_material_only": True,
        "environment_state_output_frame_must_not_return_completed_sentence": True,
        "period_tendency_from_single_record": False,
        "recovery_prescription_allowed": False,
    }
    contract_safety = {
        "public_route_changed": False,
        "request_key_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "display_gate_relaxed": False,
        "raw_text_added_to_public_metadata": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "comment_text_included": False,
        "fixed_sentence_template_used": False,
        "completed_sentence_template_used": False,
        "dictionary_returns_completed_reply": False,
        "dictionary_returned_completed_reply": False,
        "completed_reply_from_dictionary": False,
        "cause_inferred_from_category": False,
        "cause_inferred_from_emotion_strength": False,
        "personality_tendency_allowed": False,
        "period_tendency_from_single_record": False,
        "recovery_prescription_allowed": False,
        "cause_from_category": False,
        "cause_from_emotion_strength": False,
    }

    environment_state_output_frame = _build_environment_state_output_frame_projection(
        bundle.to_current_input_payload(),
        selected_relation_ids,
    )
    state_answer_surface_contract = state_answer_surface_contract_forward_meta(
        build_emlis_state_answer_surface_contract(
            bundle.to_current_input_payload(),
            environment_state_output_frame=environment_state_output_frame,
            observation_structure_material={
                "selected_relation_ids": selected_relation_ids,
                "evidence_span_ids": tuple(_evidence_ids_for_fields(evidence_ledger, matched_source_fields)),
                "bundle_field_flags": _bundle_field_flags(bundle),
                "low_information_candidate": low_information_candidate,
            },
        )
    )

    material = ObservationStructureMaterial(
        dictionary_id=structure_dictionary.dictionary_id,
        dictionary_version=structure_dictionary.dictionary_version,
        dictionary_schema_version=structure_dictionary.schema_version,
        base_dictionary=structure_dictionary.base_dictionary,
        loader_phase=structure_dictionary.loader_phase,
        selected_entry_ids=tuple(selected_entry_ids),
        selected_entry_types=tuple(selected_entry_types),
        selected_relation_ids=tuple(selected_relation_ids),
        graph_relation_ids=tuple(graph_relation_ids),
        structure_question_ids=tuple(_dedupe(question_ids)),
        matched_source_fields=tuple(matched_source_fields),
        relation_policy_ids=tuple(_relation_policy_ids(selected_relation_ids)),
        evidence_span_ids=tuple(_evidence_ids_for_fields(evidence_ledger, matched_source_fields)),
        bundle_field_flags=_bundle_field_flags(bundle),
        gate_policy=gate_policy,
        composer_policy=composer_policy,
        contract_safety=contract_safety,
        environment_state_output_frame=environment_state_output_frame,
        state_answer_surface_contract=state_answer_surface_contract,
        forbidden_inference_count=_forbidden_count(selected_entries, selected_relations),
        low_information_candidate=low_information_candidate,
    )
    assert_observation_structure_material_contract(material)
    return material


def observation_structure_material_forward_meta(value: Any) -> dict[str, Any]:
    """Return a small, text-free material payload safe for meta/trace."""

    if isinstance(value, ObservationStructureMaterial):
        meta = value.as_meta()
    elif isinstance(value, Mapping):
        meta = dict(value)
    else:
        return {}
    keys = {
        "schema_version",
        "version",
        "source_phase",
        "source_step",
        "phase",
        "dictionary_id",
        "dictionary_version",
        "dictionary_schema_version",
        "base_dictionary",
        "loader_phase",
        "passed",
        "evaluated",
        "status",
        "rejection_reasons",
        "selected_entry_ids",
        "matched_entry_ids",
        "selected_entry_types",
        "selected_relation_ids",
        "structure_relation_ids",
        "graph_relation_ids",
        "structure_question_ids",
        "constraint_ids",
        "matched_source_fields",
        "relation_policy_ids",
        "evidence_span_ids",
        "bundle_field_flags",
        "gate_policy",
        "composer_policy",
        "contract_safety",
        "environment_state_output_frame",
        "environment_state_output_frame_connected",
        "environment_state_output_frame_material_id",
        "environment_state_output_frame_schema_version",
        "environment_state_output_frame_phase",
        "environment_state_output_frame_single_record_only",
        "environment_state_output_frame_safe_projection",
        "state_answer_surface_contract",
        "state_answer_surface_contract_connected",
        "state_answer_surface_contract_material_id",
        "state_answer_surface_contract_schema_version",
        "state_answer_surface_contract_phase",
        "state_answer_surface_contract_observation_layer_connected",
        "state_answer_surface_contract_human_follow_layer_connected",
        "state_answer_surface_contract_material_only",
        "forbidden_inference_count",
        "low_information_candidate",
        "period_tendency_from_single_record",
        "recovery_prescription_allowed",
        "cause_from_category",
        "cause_from_emotion_strength",
        "structure_dictionary_loaded",
        "observation_structure_dictionary_connected",
        "structure_dictionary_material_ready",
        "input_bundle_policy_connected",
        "phase4_gate_composer_connection_ready",
        "gate_connection_ready",
        "composer_connection_ready",
        "gate_connected",
        "composer_connected",
        "dictionary_returns_completed_reply",
        "dictionary_returned_completed_reply",
        "completed_reply_from_dictionary",
        "dictionary_is_completed_reply_template",
        "dictionary_is_observation_material_only",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "comment_text_generated",
        "fixed_sentence_template_used",
        "completed_sentence_template_used",
        "display_gate_relaxed",
        "api_route_changed",
        "api_response_key_change",
        "request_key_changed",
        "response_key_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "cause_inferred_from_category",
        "cause_inferred_from_emotion_strength",
        "personality_tendency_allowed",
        "external_ai_used",
        "local_llm_used",
    }
    out = {key: copy.deepcopy(meta.get(key)) for key in keys if key in meta}
    assert_observation_structure_material_contract(out)
    return out


def observation_structure_material_gate_report(value: Any) -> dict[str, Any]:
    if isinstance(value, ObservationStructureMaterial):
        report = value.gate_report()
    elif isinstance(value, Mapping):
        meta = observation_structure_material_forward_meta(value)
        if not meta:
            return {}
        report = {
            "passed": bool(meta.get("passed", True)),
            "evaluated": True,
            "status": str(meta.get("status") or "passed"),
            "rejection_reasons": list(meta.get("rejection_reasons") or []),
            "selected_entry_ids": list(meta.get("selected_entry_ids") or []),
            "selected_relation_ids": list(meta.get("selected_relation_ids") or []),
            "constraint_ids": list(meta.get("constraint_ids") or meta.get("relation_policy_ids") or []),
            "dictionary_material_only": True,
            "dictionary_returns_completed_reply": False,
            "dictionary_returned_completed_reply": False,
            "completed_reply_from_dictionary": False,
            "display_gate_relaxed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "cause_inferred_from_category": False,
            "cause_inferred_from_emotion_strength": False,
            "personality_tendency_allowed": False,
            "period_tendency_from_single_record": False,
            "recovery_prescription_allowed": False,
            "environment_state_output_frame_connected": bool(meta.get("environment_state_output_frame_connected")),
            "environment_state_output_frame_material_id": meta.get("environment_state_output_frame_material_id") or "",
            "environment_state_output_frame_axis_presence": copy.deepcopy(dict((meta.get("environment_state_output_frame") or {}).get("axis_presence") or {})),
            "environment_state_output_frame_output_theme_ids": list(((meta.get("environment_state_output_frame") or {}).get("output_axis") or {}).get("output_theme_ids") or []),
            "state_answer_surface_contract_connected": bool(meta.get("state_answer_surface_contract_connected")),
            "state_answer_surface_contract_material_id": meta.get("state_answer_surface_contract_material_id") or "",
            "state_answer_surface_contract_gate_report": state_answer_surface_contract_gate_report(meta.get("state_answer_surface_contract") or {}) if meta.get("state_answer_surface_contract") else {},
        }
    else:
        return {}
    assert_observation_structure_material_contract(report)
    return report


def observation_structure_material_composer_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, ObservationStructureMaterial):
        payload = value.composer_payload()
    elif isinstance(value, Mapping):
        meta = observation_structure_material_forward_meta(value)
        if not meta:
            return {}
        payload = {
            "schema_version": meta.get("schema_version"),
            "source_phase": meta.get("source_phase"),
            "dictionary_id": meta.get("dictionary_id"),
            "dictionary_version": meta.get("dictionary_version"),
            "base_dictionary": meta.get("base_dictionary"),
            "selected_entry_ids": list(meta.get("selected_entry_ids") or []),
            "selected_relation_ids": list(meta.get("selected_relation_ids") or []),
            "structure_question_ids": list(meta.get("structure_question_ids") or []),
            "matched_source_fields": list(meta.get("matched_source_fields") or []),
            "relation_policy_ids": list(meta.get("relation_policy_ids") or []),
            "evidence_span_ids": list(meta.get("evidence_span_ids") or []),
            "bundle_field_flags": copy.deepcopy(dict(meta.get("bundle_field_flags") or {})),
            "gate_policy": copy.deepcopy(dict(meta.get("gate_policy") or {})),
            "composer_policy": copy.deepcopy(dict(meta.get("composer_policy") or {})),
            "forbidden_inference_count": int(meta.get("forbidden_inference_count") or 0),
            "low_information_candidate": bool(meta.get("low_information_candidate")),
            "environment_state_output_frame": copy.deepcopy(dict(meta.get("environment_state_output_frame") or {})),
            "environment_state_output_frame_connected": bool(meta.get("environment_state_output_frame_connected")),
            "environment_state_output_frame_material_id": meta.get("environment_state_output_frame_material_id") or "",
            "environment_state_output_frame_schema_version": meta.get("environment_state_output_frame_schema_version") or "",
            "environment_state_output_frame_single_record_only": bool(meta.get("environment_state_output_frame_single_record_only")),
            "state_answer_surface_contract": state_answer_surface_contract_composer_payload(meta.get("state_answer_surface_contract") or {}) if meta.get("state_answer_surface_contract") else {},
            "state_answer_surface_contract_connected": bool(meta.get("state_answer_surface_contract_connected")),
            "state_answer_surface_contract_material_id": meta.get("state_answer_surface_contract_material_id") or "",
            "state_answer_surface_contract_schema_version": meta.get("state_answer_surface_contract_schema_version") or "",
            "period_tendency_from_single_record": False,
            "recovery_prescription_allowed": False,
            "dictionary_is_observation_material_only": True,
            "dictionary_returns_completed_reply": False,
            "dictionary_returned_completed_reply": False,
            "completed_reply_from_dictionary": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "cause_inferred_from_category": False,
            "cause_inferred_from_emotion_strength": False,
            "personality_tendency_allowed": False,
        }
    else:
        return {}
    assert_observation_structure_material_contract(payload)
    return payload


def assert_observation_structure_material_contract(value: Any, *, source: str = "observation_structure_material") -> None:
    if isinstance(value, ObservationStructureMaterial):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    if _clean(value.get("dictionary_id")) not in {"", OBSERVATION_STRUCTURE_DICTIONARY_ID}:
        raise ValueError(f"{source} has unexpected dictionary_id")
    if _clean(value.get("base_dictionary")) not in {"", OBSERVATION_STRUCTURE_DICTIONARY_BASE}:
        raise ValueError(f"{source} has unexpected base_dictionary")
    if _clean(value.get("dictionary_schema_version")) not in {"", OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION}:
        raise ValueError(f"{source} has unexpected dictionary_schema_version")
    if _clean(value.get("loader_phase")) not in {"", OBSERVATION_STRUCTURE_DICTIONARY_LOADER_PHASE}:
        raise ValueError(f"{source} has unexpected loader_phase")
    if value.get("dictionary_is_observation_material_only") is False:
        raise ValueError(f"{source} must keep dictionary_is_observation_material_only=true when present")
    if value.get("display_gate_relaxed") is True:
        raise ValueError(f"{source} must not relax Display Gate")
    state_answer_contract = value.get("state_answer_surface_contract")
    if state_answer_contract:
        assert_emlis_state_answer_surface_contract(state_answer_contract, source=f"{source}.state_answer_surface_contract")
    if _clean(value.get("state_answer_surface_contract_material_id")) not in {"", EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID}:
        raise ValueError(f"{source} has unexpected state_answer_surface_contract_material_id")
    if _clean(value.get("state_answer_surface_contract_schema_version")) not in {"", EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION}:
        raise ValueError(f"{source} has unexpected state_answer_surface_contract_schema_version")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


build_emlis_ai_observation_structure_material = build_observation_structure_material
assert_emlis_ai_observation_structure_material_contract = assert_observation_structure_material_contract

__all__ = [
    "OBSERVATION_STRUCTURE_MATERIAL_SCHEMA_VERSION",
    "OBSERVATION_STRUCTURE_MATERIAL_PHASE",
    "ObservationStructureMaterial",
    "build_observation_structure_material",
    "build_emlis_ai_observation_structure_material",
    "observation_structure_material_forward_meta",
    "observation_structure_material_gate_report",
    "observation_structure_material_composer_payload",
    "assert_observation_structure_material_contract",
    "assert_emlis_ai_observation_structure_material_contract",
]
