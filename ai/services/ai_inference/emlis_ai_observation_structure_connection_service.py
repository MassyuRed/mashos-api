# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 Gate / Composer connection for the Emlis structure dictionary.

The validated structure dictionary is connected as text-free observation
material.  This module never creates public comment text, never returns a
completed reply sentence, and never changes public API / DB / RN contracts.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_observation_reply_contract import (
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
)
from emlis_ai_observation_structure_dictionary_loader import (
    OBSERVATION_STRUCTURE_DICTIONARY_ID,
    OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION,
    ObservationStructureDictionary,
    load_observation_structure_dictionary,
)

OBSERVATION_STRUCTURE_CONNECTION_VERSION: Final = "emlis.observation_structure_connection.v1"
OBSERVATION_STRUCTURE_CONNECTION_PHASE: Final = "Phase4_Gate_Composer_Connection"

_SPACE_RE: Final = re.compile(r"\s+")
_GAP_WORD_RE: Final = re.compile(r"(大丈夫|平気|なんでもない|何でもない|大したことない|大丈夫なはず|まあいいか)")
_LOW_INFO_RE: Final = re.compile(r"^(無理|もう無理|しんどい|限界|疲れた|怖い|こわい|やばい|もう嫌だ|もういやだ)$")
_STATE_RE: Final = re.compile(r"(無理|限界|しんど|疲れ|怖|こわ|不安|嫌|いや|つら|辛|大丈夫|平気|なんでもない)")
_DISCREPANCY_RE: Final = re.compile(r"(本当は|ほんとは|嫌だった|いやだった|笑って対応|我慢|隠|耐え|言えなかった|合わせた|平気なふり|大丈夫なふり)")
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
_FORBIDDEN_PAYLOAD_KEYS: Final = frozenset({
    "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
    "input", "input_text", "inputText", "user_input", "userInput", "current_input", "currentInput",
    "memo", "memo_action", "memoText", "memoAction", "thought_text", "action_text",
    "comment_text", "commentText", "reply_text", "replyText", "surface_text", "realized_text",
    "completed_reply_text", "body", "text", "definition", "default_direction", "receive_direction", "strong_hand_direction",
})
_FORBIDDEN_TRUE_FLAGS: Final = frozenset({
    "raw_input_included", "raw_text_included", "comment_text_included", "comment_text_body_included",
    "comment_text_generated", "public_status_extended", "observation_status_enum_extended",
    "api_response_key_change", "response_key_changed", "api_route_changed", "db_physical_name_changed", "rn_visible_contract_changed",
    "rn_visible_title_changed", "display_gate_relaxed", "reader_gate_relaxed", "grounding_gate_relaxed",
    "template_gate_relaxed", "gate_relaxed", "fixed_fallback_used", "fixed_sentence_template_used",
    "completed_reply_from_dictionary", "dictionary_returned_completed_reply", "dictionary_returns_completed_reply", "external_ai_used", "local_llm_used",
    "user_fact_may_promote_to_eligible", "promote_low_info_to_eligible", "assert_current_event_from_user_fact",
    "cause_inferred_from_category", "cause_inferred_from_emotion_strength", "personality_tendency_allowed",
})


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


def _joined(bundle: Any) -> str:
    return _clean("。".join(part for part in (bundle.thought_text, bundle.action_text) if _clean(part)))


def _compact_len(value: str) -> int:
    return len(re.sub(r"[\s\u3000。．、，,.!！?？:：;；\-ー_\/\\]+", "", value or ""))


def _span_id(span: Any, index: int) -> str:
    if isinstance(span, Mapping):
        return _clean(span.get("span_id") or span.get("id") or span.get("ref_id")) or f"s{index + 1}"
    return _clean(getattr(span, "span_id", None) or getattr(span, "id", None) or getattr(span, "ref_id", None)) or f"s{index + 1}"


def _entry_matches(entry: Any, bundle: Any, joined_text: str) -> bool:
    entry_type = _clean(getattr(entry, "entry_type", ""))
    words = list(getattr(entry, "input_words", ()) or ())
    emotion_types = {emotion.type for emotion in bundle.emotions}
    if entry_type == "special_emotion_mode" and any(word in emotion_types for word in words):
        return True
    if entry_type == "emotion_relation" and len(bundle.emotions) >= 2:
        return True
    if entry_type == "thought_action_relation" and _has_thought_action_gap(bundle):
        return True
    if entry_type == "category_relation" and len(bundle.categories) >= 2:
        return True
    if entry_type == "prompt_policy" and _is_low_information(bundle):
        return True
    return any(_clean(word) and _clean(word) in joined_text for word in words)


def _has_gap_word(bundle: Any) -> bool:
    return bool(_GAP_WORD_RE.search(_joined(bundle)))


def _has_thought_action_gap(bundle: Any) -> bool:
    return bool(bundle.thought_text and bundle.action_text and _DISCREPANCY_RE.search(_joined(bundle)))


def _has_unexpressed_output_stop(bundle: Any) -> bool:
    return bool(_UNEXPRESSED_OUTPUT_STOP_RE.search(_joined(bundle)))


def _has_self_shape_alignment(bundle: Any) -> bool:
    return bool(_SELF_SHAPE_ALIGNMENT_RE.search(_joined(bundle)))


def _has_action_conversion_history(bundle: Any) -> bool:
    return bool(_ACTION_CONVERSION_HISTORY_RE.search(_joined(bundle)))


def _has_conversion_history_closure_evidence(bundle: Any) -> bool:
    return bool(_has_action_conversion_history(bundle) and _CONVERSION_HISTORY_CLOSURE_RE.search(_joined(bundle)))


def _has_unformed_self_insight(bundle: Any) -> bool:
    return bool(_UNFORMED_SELF_INSIGHT_RE.search(_joined(bundle)))


def _has_priority_pressure_evidence(bundle: Any) -> bool:
    return bool(_PRIORITY_PRESSURE_EVIDENCE_RE.search(_joined(bundle)))


def _has_load_or_fatigue_evidence(bundle: Any) -> bool:
    return bool(_LOAD_OR_FATIGUE_EVIDENCE_RE.search(_joined(bundle)))


def _filter_relation_ids_by_evidence(relation_ids: Sequence[str], *, bundle: Any, low_information: bool) -> list[str]:
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
        if relation_id == "thought_action_discrepancy" and not _has_thought_action_gap(bundle):
            continue
        if relation_id == "conversion_history_closure" and not _has_conversion_history_closure_evidence(bundle):
            continue
        if relation_id == "priority_pressure" and not _has_priority_pressure_evidence(bundle):
            continue
        if relation_id == "load_accumulation" and not _has_load_or_fatigue_evidence(bundle):
            continue
        if relation_id in {"low_information_weight", "user_agency_prompt"} and not low_information:
            continue
        out.append(relation_id)
    return _dedupe(out)


def _has_category_overlap_evidence(bundle: Any) -> bool:
    categories = set(getattr(bundle, "categories", ()) or ())
    joined = _joined(bundle)
    if not joined or len(categories) < 2:
        return False
    if {"仕事", "健康"}.issubset(categories) and _WORK_HEALTH_OVERLAP_RE.search(joined):
        return True
    if {"仕事", "人間関係"}.issubset(categories) and _WORK_RELATION_OVERLAP_RE.search(joined):
        return True
    return False


def _has_textual_target(bundle: Any) -> bool:
    # Category labels are topic directions, not causes; only memo/action text can reduce low-information status here.
    return bool(_TEXTUAL_TARGET_RE.search(_joined(bundle)))


def _is_low_information(bundle: Any) -> bool:
    joined = _joined(bundle)
    if not joined:
        return True
    if bundle.action_text:
        return False
    compact = _compact_len(joined)
    if _has_textual_target(bundle):
        return False
    return bool(compact <= 10 and (_LOW_INFO_RE.match(joined) or _STATE_RE.search(joined)))


def _relations_from_entries(entries: Sequence[Any], *, bundle: Any, low_information: bool) -> list[str]:
    out: list[str] = []
    for entry in entries:
        out.extend(
            _filter_relation_ids_by_evidence(
                getattr(entry, "relation_candidates", ()) or (),
                bundle=bundle,
                low_information=low_information,
            )
        )
    return _dedupe(out)


def _roles_for_relations(relation_ids: Sequence[str]) -> list[str]:
    roles: list[str] = []
    ids = set(relation_ids)
    if ids.intersection({"state_text_gap", "emotion_nesting", "low_information_weight"}):
        roles.append("state")
    if ids.intersection(
        {
            "thought_action_discrepancy",
            "category_overlap",
            "category_parallel",
            "unexpressed_output_stop",
            "self_shape_alignment",
            "action_conversion_history",
            "conversion_history_closure",
        }
    ):
        roles.append("relation_graph")
    if ids.intersection({"thought_action_discrepancy", "unexpressed_output_stop", "self_shape_alignment", "action_conversion_history"}):
        roles.extend(["target", "contrast"])
    if ids.intersection({"desire_stagnation", "action_blocked", "pressure_gap"}):
        roles.extend(["wish", "blockage"])
    if ids.intersection({"self_insight_discovery", "unformed_self_insight"}):
        roles.append("self_awareness")
    if "unformed_self_insight" in ids:
        roles.append("state")
    return _dedupe(roles)


def _confidence_hint(relation_ids: Sequence[str], low_information: bool) -> float:
    ids = set(relation_ids)
    if low_information:
        return 0.33
    if "thought_action_discrepancy" in ids:
        return 0.62
    if "category_overlap" in ids:
        return 0.52
    if ids.intersection({"action_conversion_history", "conversion_history_closure", "self_shape_alignment", "unexpressed_output_stop"}):
        return 0.50
    if "unformed_self_insight" in ids:
        return 0.44
    if ids.intersection({"desire_stagnation", "action_blocked", "pressure_gap"}):
        return 0.50
    if "state_text_gap" in ids:
        return 0.44
    if "low_information_weight" in ids:
        return 0.33
    return 0.0


def _unknown_slots(low_information: bool, relation_ids: Sequence[str]) -> list[str]:
    # `low_information_weight` can be a dictionary relation candidate for words such as
    # 「怖い」, but it must not by itself downgrade a targeted input to low-information.
    # Gate unknown-slot pressure is emitted only when the current input bundle is actually
    # low-information after checking thought/action/category/emotion material.
    if low_information:
        return [UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION, UNKNOWN_SLOT_CAUSE]
    if "state_text_gap" in set(relation_ids):
        return [UNKNOWN_SLOT_CURRENT_FEELING_TARGET]
    return []


@dataclass(frozen=True)
class ObservationStructureConnection:
    selected_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    selected_relation_ids: tuple[str, ...] = field(default_factory=tuple)
    gate_signal_roles: tuple[str, ...] = field(default_factory=tuple)
    gate_known_fragments: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    low_information_unknown_slots: tuple[str, ...] = field(default_factory=tuple)
    relation_confidence_hint: float = 0.0
    current_input_evidence_bonus: float = 0.0
    composer_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    composer_relation_ids: tuple[str, ...] = field(default_factory=tuple)
    composer_material_roles: tuple[str, ...] = field(default_factory=tuple)
    forbidden_inference_entry_ids: tuple[str, ...] = field(default_factory=tuple)
    forbidden_inference_relation_ids: tuple[str, ...] = field(default_factory=tuple)
    supporting_evidence_span_ids: tuple[str, ...] = field(default_factory=tuple)
    dictionary_version: str = ""
    dictionary_id: str = OBSERVATION_STRUCTURE_DICTIONARY_ID
    schema_version: str = OBSERVATION_STRUCTURE_CONNECTION_VERSION

    def as_meta(self) -> dict[str, Any]:
        meta = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "source_phase": OBSERVATION_STRUCTURE_CONNECTION_PHASE,
            "source_step": OBSERVATION_STRUCTURE_CONNECTION_PHASE,
            "observation_structure_connection_ready": True,
            "phase4_gate_composer_connection_ready": True,
            "dictionary_id": self.dictionary_id,
            "dictionary_schema_version": OBSERVATION_STRUCTURE_DICTIONARY_SCHEMA_VERSION,
            "dictionary_version": self.dictionary_version,
            "selected_entry_ids": list(self.selected_entry_ids),
            "selected_relation_ids": list(self.selected_relation_ids),
            "supporting_evidence_span_ids": list(self.supporting_evidence_span_ids),
            "gate_connected": True,
            "composer_connected": True,
            "gate_relation_ids": list(self.selected_relation_ids),
            "gate_signal_roles": list(self.gate_signal_roles),
            "gate_known_fragments": [dict(item) for item in self.gate_known_fragments],
            "low_information_unknown_slots": list(self.low_information_unknown_slots),
            "relation_confidence_hint": round(float(self.relation_confidence_hint or 0.0), 4),
            "current_input_evidence_bonus": round(float(self.current_input_evidence_bonus or 0.0), 4),
            "composer_entry_ids": list(self.composer_entry_ids),
            "composer_relation_ids": list(self.composer_relation_ids),
            "composer_material_roles": list(self.composer_material_roles),
            "forbidden_inference_entry_ids": list(self.forbidden_inference_entry_ids),
            "forbidden_inference_relation_ids": list(self.forbidden_inference_relation_ids),
            "dictionary_material_only": True,
            "dictionary_returns_completed_reply": False,
            "dictionary_returned_completed_reply": False,
            "completed_reply_from_dictionary": False,
            "surface_policy_returned_as_text": False,
            "category_used_as_cause": False,
            "cause_inferred_from_category": False,
            "emotion_strength_used_as_cause": False,
            "cause_inferred_from_emotion_strength": False,
            "low_information_event_filled": False,
            "user_agency_prompt_preserved": True,
            "comment_text_generated": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "response_key_changed": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "gate_relaxed": False,
            "fixed_fallback_used": False,
            "fixed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "unsupported_assertion_allowed": False,
            "personality_tendency_allowed": False,
            "user_fact_may_promote_to_eligible": False,
            "assert_current_event_from_user_fact": False,
            "user_fact_used_for_current_event_assertion": False,
        }
        assert_observation_structure_connection_contract(meta)
        return meta


def build_observation_structure_connection(
    *,
    current_input: Any,
    evidence_ledger: Sequence[Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    observation_graph: Any = None,
    observation_dictionary: ObservationStructureDictionary | None = None,
    dictionary: ObservationStructureDictionary | None = None,
) -> ObservationStructureConnection:
    del observation_graph  # Relation graph material is already represented by the caller's Gate path.
    dictionary_obj = observation_dictionary or dictionary or load_observation_structure_dictionary()
    bundle = build_emlis_current_input_bundle(current_input)
    joined = _joined(bundle)
    selected_spans = evidence_ledger if evidence_ledger is not None else evidence_spans
    selected_spans = list(selected_spans) if selected_spans is not None else list(build_evidence_ledger(bundle.to_current_input_payload()))
    entry_ids: list[str] = []
    entries: list[Any] = []
    for entry in dictionary_obj.entries:
        if _entry_matches(entry, bundle, joined):
            entry_ids.append(entry.entry_id)
            entries.append(entry)
    low_information = _is_low_information(bundle)
    relation_ids = _relations_from_entries(entries, bundle=bundle, low_information=low_information)
    if _has_gap_word(bundle) and bundle.emotions:
        relation_ids.append("state_text_gap")
    if len(bundle.emotions) >= 2:
        relation_ids.append("emotion_nesting")
    if len(bundle.categories) >= 2:
        relation_ids.append("category_parallel")
    if _has_category_overlap_evidence(bundle):
        relation_ids.append("category_overlap")
    else:
        relation_ids = [relation_id for relation_id in relation_ids if relation_id != "category_overlap"]
    if _has_thought_action_gap(bundle):
        relation_ids.append("thought_action_discrepancy")
    if any(emotion.type == "自己理解" for emotion in bundle.emotions):
        relation_ids.append("self_insight_discovery")
    if low_information:
        relation_ids.extend(["low_information_weight", "user_agency_prompt"])
    relation_set = {relation.relation_id for relation in dictionary_obj.relations}
    relation_ids = tuple(
        item
        for item in _filter_relation_ids_by_evidence(
            _dedupe(relation_ids),
            bundle=bundle,
            low_information=low_information,
        )
        if item in relation_set
    )
    selected_entry_ids = tuple(_dedupe(entry_ids))
    gate_fragments = tuple(
        {
            "evidence_span_id": f"structure_dictionary:{relation_id}",
            "source_field": "observation_structure_dictionary",
            "role": "relation_graph",
            "confidence": 0.33,
            "current_input_evidence": False,
            "dictionary_material_only": True,
            "raw_input_included": False,
        }
        for relation_id in relation_ids
    )
    roles = tuple(_roles_for_relations(relation_ids))
    return ObservationStructureConnection(
        selected_entry_ids=selected_entry_ids,
        selected_relation_ids=relation_ids,
        gate_signal_roles=roles,
        gate_known_fragments=gate_fragments,
        low_information_unknown_slots=tuple(_unknown_slots(low_information, relation_ids)),
        relation_confidence_hint=_confidence_hint(relation_ids, low_information),
        current_input_evidence_bonus=0.0,
        composer_entry_ids=selected_entry_ids,
        composer_relation_ids=relation_ids,
        composer_material_roles=tuple(_dedupe(["input_organization", "user_agency_prompt"] if low_information else ["input_organization"])),
        forbidden_inference_entry_ids=selected_entry_ids,
        forbidden_inference_relation_ids=relation_ids,
        supporting_evidence_span_ids=tuple(_span_id(span, index) for index, span in enumerate(selected_spans)),
        dictionary_version=dictionary_obj.dictionary_version,
    )


def observation_structure_connection_forward_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, ObservationStructureConnection):
        return value.as_meta()
    if isinstance(value, Mapping):
        meta = dict(value)
    else:
        return {}
    assert_observation_structure_connection_contract(meta)
    return meta


def observation_structure_connection_forward_composer_meta(value: Any) -> dict[str, Any]:
    meta = observation_structure_connection_forward_meta(value)
    return {
        "schema_version": meta.get("schema_version") or OBSERVATION_STRUCTURE_CONNECTION_VERSION,
        "source_phase": meta.get("source_phase") or OBSERVATION_STRUCTURE_CONNECTION_PHASE,
        "dictionary_id": meta.get("dictionary_id") or OBSERVATION_STRUCTURE_DICTIONARY_ID,
        "selected_entry_ids": list(meta.get("composer_entry_ids") or meta.get("selected_entry_ids") or []),
        "selected_relation_ids": list(meta.get("composer_relation_ids") or meta.get("selected_relation_ids") or []),
        "composer_material_roles": list(meta.get("composer_material_roles") or []),
        "forbidden_inference_relation_ids": list(meta.get("forbidden_inference_relation_ids") or []),
        "observation_material_only": True,
        "dictionary_must_not_return_completed_sentence": True,
        "dictionary_returns_completed_reply": False,
        "dictionary_returned_completed_reply": False,
        "completed_reply_from_dictionary": False,
        "surface_realizer_owns_natural_language": True,
        "must_not_create_cause_without_evidence": True,
        "must_not_personality_diagnose": True,
        "cause_inferred_from_category": False,
        "cause_inferred_from_emotion_strength": False,
        "personality_tendency_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "display_gate_relaxed": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }


def observation_structure_connection_forward_material_meta(value: Any) -> dict[str, Any]:
    return observation_structure_connection_forward_composer_meta(value)


def assert_observation_structure_connection_contract(value: Any, *, source: str = "observation_structure_connection") -> None:
    if isinstance(value, ObservationStructureConnection):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must remain meta-only and must not include raw/comment text keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


def build_observation_structure_connection_meta(**kwargs: Any) -> dict[str, Any]:
    return build_observation_structure_connection(**kwargs).as_meta()


__all__ = [
    "OBSERVATION_STRUCTURE_CONNECTION_PHASE",
    "OBSERVATION_STRUCTURE_CONNECTION_VERSION",
    "ObservationStructureConnection",
    "assert_observation_structure_connection_contract",
    "build_observation_structure_connection",
    "build_observation_structure_connection_meta",
    "observation_structure_connection_forward_meta",
    "observation_structure_connection_forward_composer_meta",
    "observation_structure_connection_forward_material_meta",
]
