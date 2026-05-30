# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 10 Cross Gate for EmlisAI two-stage reception surfaces.

The gate inspects a candidate ``comment_text`` in memory and returns only
small reason codes and booleans. It never returns section bodies, raw input,
raw evidence, memo, memo_action, or the candidate text itself.
"""

from collections.abc import Iterable, Mapping
import copy
import json
import re
from typing import Any, Final

from emlis_ai_two_stage_applicability import build_two_stage_applicability_decision

from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta

EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis_ai_two_stage_reception.cross_gate.v1"
)
EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID: Final = (
    "emlis_ai_two_stage_reception_cross_gate"
)
EMLIS_AI_TWO_STAGE_RECEPTION_GATE_PHASE: Final = "Phase10_two_stage_reception_cross_gate"
EMLIS_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION: Final = EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION
EMLIS_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID: Final = EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID
EMLIS_TWO_STAGE_RECEPTION_GATE_PHASE: Final = EMLIS_AI_TWO_STAGE_RECEPTION_GATE_PHASE

OBSERVATION_LABEL: Final = "見えたこと："
RECEPTION_LABEL: Final = "Emlisから："

_SPACE_RE: Final = re.compile(r"\s+")
_SENTENCE_RE: Final = re.compile(r"[。！？!?]+|[\r\n]+")
_OBSERVATION_COMMENT_TONE_RE: Final = re.compile(
    r"(?:うわ|嫌でしたね|自然です|よかったですね|嬉しいですね|大丈夫です|安心してください|"
    r"つらかったですね|しんどかったですね|それは嫌|それは怖)"
)
_RECEPTION_NEW_FACT_OVERCLAIM_RE: Final = re.compile(
    r"(?:原因は[^。！？!?\n]{0,20}(?:です|でした)|本当の原因|理由はひとつ|"
    r"いつも[^。！？!?\n]{0,24}(?:そう|同じ|傾向)|毎回[^。！？!?\n]{0,24}(?:そう|同じ|傾向)|"
    r"ずっと[^。！？!?\n]{0,24}(?:そう|同じ|傾向)|[^。！？!?\n]{0,24}が原因(?:です|でした)?)"
)
_DIAGNOSIS_RE: Final = re.compile(r"(?:診断|治療|病気|症状|トラウマ|PTSD|医学的|心理学的|発達障害|ADHD|うつ|鬱)")
_PERSONALITY_CLAIM_RE: Final = re.compile(
    r"(?:あなたは(?:本当は)?(?:すごい人|素晴らしい人|優しい人|強い人|弱い人ではありません|"
    r"ダメな人|駄目な人|中途半端な人)|性格だから|本質的に|本質は[^。！？!?\n]{0,20}です)"
)
_ACTION_INSTRUCTION_RE: Final = re.compile(
    r"(?:してください|しましょう|するべき|しなければ|しなくてはいけない|行動しましょう|"
    r"連絡しましょう|相談しましょう|休みましょう|自信を持ちましょう|距離を取(?:った|る)方がいい|"
    r"我慢しなくていい|我慢しなくてもいい)"
)
_TARGET_JUDGEMENT_AGREEMENT_RE: Final = re.compile(
    r"(?:(?:その人|あの人|相手|上司|彼|彼女|会社|職場|おじさん)[^。！？!?\n]{0,24}(?:最低|悪い|ひどい|おかしい|間違っている|敵)|"
    r"あなたの怒りは(?:正しい|当然)|相手が悪い|上司が悪い|その人は最低)"
)
_QUESTION_ESCAPE_RE: Final = re.compile(
    r"(?:何があったか[^。！？!?\n]{0,16}残してみませんか|何がありましたか|詳しく残せそうなら|"
    r"まだ詳しい出来事までは見えません|出来事までは見えません)"
)
_EVENT_HINT_EMOTION_OVERCLAIM_RE: Final = re.compile(
    r"(?:怖かったですね|恐怖でしたね|怖さと怒りが残っている|怖さが残るのは自然|怒りが残るのは自然|気持ち悪かったですね|嫌でしたね|不快でしたね)"
)
_EVENT_HINT_RISK_OVERCLAIM_RE: Final = re.compile(r"(?:危険な目に遭いました(?:ね)?|危険な場面でした|トラウマになりそう|トラウマになった|実際に危険でした)")
_UNKNOWN_WORD_ASSERTION_RE: Final = re.compile(
    r"(?:立ちションとは|立ちションは[^。！？!?\n]{0,24}(?:意味|行為|犯罪|迷惑行為)|つまり立ちション)"
)
_MALFORMED_NOMINALIZATION_PATTERNS: Final = (
    re.compile(r"(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|取らなければ)こと(?:$|[もがはにをでへ、。,.])"),
    re.compile(r"(?:予感|気配|予定|必要|つもり|はず|可能性|見込み|感じ|得意|好き)こと(?:$|[もがはにをでへ、。,.])"),
    re.compile(r"(?:ことこと|頑張りたいって気持ちになってこと|私のここが好き[^。！？!?\n]{0,24}得意こと)"),
)
_INTERNAL_ROLE_LABEL_LEAK_RE: Final = re.compile(
    r"(?:\bachievement\b|positive[\s_]+state|perfection[\s_]+fear|pressure[\s_]+or[\s_]+limit|role_)",
    re.IGNORECASE,
)
_RELATION_SKELETON_RE: Final = re.compile(
    r"(?:同じ流れが同じ場所|同じ流れ|同じ場所|関係骨格|一つの要素だけではありません|"
    r"今見えている範囲は一つの要素だけではありません|状態が一色ではありません|片方だけに減らさず|"
    r"片方だけに寄らず|別々の向き|重なりを保っています|一方向には決まりきっていません|"
    r"先を考え続ける流れ|pressure\s+or\s+limit|重なりとして[^。！？!?\n]{0,80}として重なり|"
    r"explicit negative reaction|daily event fact|pressure_or_limit|anticipation_loop)",
    re.IGNORECASE,
)
_TEMPLATE_ECHO_RE: Final = re.compile(r"(.{4,24})\1{2,}")
_STABLE_GROWTH_OR_RECOVERY_ASSERTION_RE: Final = re.compile(
    r"(?:完全に回復しています|もう大丈夫(?:です)?|成長しています|自立できます)"
)
_ANALYTIC_OVER_EXPLAIN_RE: Final = re.compile(r"(?:構造|関係性|要素|分類|パターン|傾向|深層|価値線)")

_FORBIDDEN_PAYLOAD_KEYS: Final = frozenset({
    "input", "input_text", "inputText", "user_input", "userInput", "current_input", "currentInput",
    "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText", "memo", "memo_action",
    "memoText", "memoAction", "comment_text", "commentText", "candidate_comment_text", "public_comment_text",
    "reply_text", "replyText", "surface_text", "realized_text", "observation_text", "observationText",
    "reception_text", "receptionText", "evidence_text", "raw_quote", "raw_quotes", "body", "text", "sentence", "sentences",
})
_FORBIDDEN_TRUE_FLAGS: Final = frozenset({
    "raw_input_included", "raw_text_included", "input_text_included", "comment_text_included", "comment_text_body_included",
    "observation_text_included", "reception_text_included", "section_body_included", "public_response_key_added",
    "public_response_key_change", "response_shape_changed", "api_route_changed", "db_physical_name_changed",
    "rn_visible_contract_changed", "display_gate_relaxed", "gate_relaxed", "external_ai_used", "local_llm_used",
    "fixed_sentence_template_added", "fixed_sentence_template_used",
})


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


def _section_sentence_count(value: str) -> int:
    return len([item for item in (_clean(chunk) for chunk in _SENTENCE_RE.split(value)) if item])


def _split_sections(comment_text: Any) -> dict[str, Any]:
    surface = str(comment_text or "")
    observation_label_count = surface.count(OBSERVATION_LABEL)
    reception_label_count = surface.count(RECEPTION_LABEL)
    labels_present = observation_label_count == 1 and reception_label_count == 1
    observation_index = surface.find(OBSERVATION_LABEL)
    reception_index = surface.find(RECEPTION_LABEL)
    label_order_valid = labels_present and observation_index < reception_index
    observation_section = ""
    reception_section = ""
    if label_order_valid:
        observation_section = surface[observation_index + len(OBSERVATION_LABEL) : reception_index].strip()
        reception_section = surface[reception_index + len(RECEPTION_LABEL) :].strip()
    return {
        "labels_present": labels_present,
        "observation_label_count": observation_label_count,
        "reception_label_count": reception_label_count,
        "label_order_valid": label_order_valid,
        "observation_section_non_empty": bool(_clean(observation_section)),
        "reception_section_non_empty": bool(_clean(reception_section)),
        "observation_section": observation_section,
        "reception_section": reception_section,
    }


def _contract_from_inputs(*, state_answer_surface_contract: Any = None, composer_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    direct = _as_mapping(state_answer_surface_contract)
    if direct:
        return _deepcopy_mapping(direct)
    meta = _as_mapping(composer_meta)
    for key in ("state_answer_surface_contract", "emlis_state_answer_surface_contract", "state_answer_contract"):
        found = _as_mapping(meta.get(key))
        if found:
            return _deepcopy_mapping(found)
    for container_key in ("composer_meta", "composition_contract", "diagnostic_summary", "gate_trace"):
        container = _as_mapping(meta.get(container_key))
        for key in ("state_answer_surface_contract", "emlis_state_answer_surface_contract", "state_answer_contract"):
            found = _as_mapping(container.get(key))
            if found:
                return _deepcopy_mapping(found)
    return {}


def _shared_evidence_from_inputs(*, shared_reception_evidence: Any = None, state_answer_surface_contract: Mapping[str, Any] | None = None, composer_meta: Mapping[str, Any] | None = None, current_input: Any = None) -> dict[str, Any]:
    direct = _as_mapping(shared_reception_evidence)
    if direct:
        return _deepcopy_mapping(direct)
    contract = _as_mapping(state_answer_surface_contract)
    for key in ("shared_reception_evidence", "reception_shared_evidence"):
        found = _as_mapping(contract.get(key))
        if found:
            return _deepcopy_mapping(found)
    reception_mode = _as_mapping(contract.get("reception_mode"))
    if reception_mode:
        return {
            "event_fact_present": bool(reception_mode.get("event_fact_present")),
            "reaction_present": bool(reception_mode.get("reaction_present")),
            "event_hint_ids": _dedupe(reception_mode.get("event_hint_ids") or []),
            "explicit_reaction_cue_ids": _dedupe(reception_mode.get("explicit_reaction_cue_ids") or []),
            "general_dictionary_used": False,
        }
    meta = _as_mapping(composer_meta)
    for key in ("shared_reception_evidence", "reception_shared_evidence"):
        found = _as_mapping(meta.get(key))
        if found:
            return _deepcopy_mapping(found)
    current = _as_mapping(current_input)
    if current:
        memo = _clean(current.get("memo"))
        action = _clean(current.get("memo_action"))
        emotions = [
            _clean(item.get("type") if isinstance(item, Mapping) else item)
            for item in _listify(current.get("emotion_details") or current.get("emotions") or [])
        ]
        reaction_surface = " ".join([memo, *emotions])
        reaction_present = bool(re.search(r"(?:怖|恐怖|怒り|イライラ|気持ち悪|不快|嫌|嬉|ほっと|不安|しんど)", reaction_surface))
        event_hint_ids = []
        if re.search(r"(?:立ちション|すれ違|外|通り|おじさん)", action):
            event_hint_ids.append("public_unpleasant_encounter")
        return {
            "event_fact_present": bool(action),
            "reaction_present": reaction_present,
            "event_hint_ids": event_hint_ids,
            "explicit_reaction_cue_ids": [],
            "general_dictionary_used": False,
            "unknown_word_meaning_asserted": False,
        }
    return {}


def _current_input_evidence(current_input: Any) -> dict[str, Any]:
    current = _as_mapping(current_input)
    memo = _clean(current.get("memo") or current.get("memo_text") or current.get("text"))
    action = _clean(current.get("memo_action") or current.get("action") or current.get("memoAction"))
    emotion_details = _listify(current.get("emotion_details") or [])
    emotions = _listify(current.get("emotions") or [])
    event_hint_ids: list[str] = []
    if any(marker in action for marker in ("立ちション", "すれ違", "おじさん")):
        event_hint_ids.append("public_unpleasant_encounter")
    return {
        "event_fact_present": bool(action),
        "reaction_present": bool(memo or emotion_details or emotions),
        "event_hint_ids": event_hint_ids,
    }


def _merge_evidence(primary: Mapping[str, Any], fallback: Mapping[str, Any]) -> dict[str, Any]:
    merged = _deepcopy_mapping(primary)
    for key, value in fallback.items():
        if key not in merged or merged.get(key) in (None, "", [], ()): 
            merged[key] = value
    if not merged.get("event_hint_ids") and fallback.get("event_hint_ids"):
        merged["event_hint_ids"] = list(fallback.get("event_hint_ids") or [])
    return merged


def _mode_id_from_inputs(*, reception_mode: Any = None, state_answer_surface_contract: Mapping[str, Any] | None = None, composer_meta: Mapping[str, Any] | None = None) -> str:
    if isinstance(reception_mode, str):
        return _clean(reception_mode)
    direct = _as_mapping(reception_mode)
    for key in ("reception_mode_id", "selected_reception_mode_id", "mode_id", "reception_mode"):
        value = _clean(direct.get(key))
        if value:
            return value
    contract = _as_mapping(state_answer_surface_contract)
    for container_key in ("reception_mode", "reception_section_material", "two_stage_reception"):
        container = _as_mapping(contract.get(container_key))
        for key in ("reception_mode_id", "selected_reception_mode_id", "mode_id", "reception_mode"):
            value = _clean(container.get(key))
            if value:
                return value
    meta = _as_mapping(composer_meta)
    for container_key in ("reception_mode", "reception_mode_summary", "reception_section_material"):
        container = _as_mapping(meta.get(container_key))
        for key in ("reception_mode_id", "selected_reception_mode_id", "mode_id", "reception_mode"):
            value = _clean(container.get(key))
            if value:
                return value
    return ""


def _mode_family(mode_id: str) -> str:
    if mode_id.startswith("daily_"):
        return "daily_reception"
    if mode_id in {"self_denial_support", "uncertainty_support", "self_confidence_uncertainty"}:
        return "self_negative_or_uncertainty"
    if mode_id == "structure_question_observation":
        return "structure_question"
    return mode_id or "unknown"


def _section_shape_reasons(shape: Mapping[str, Any], *, two_stage_required: bool) -> list[str]:
    reasons: list[str] = []
    if not two_stage_required and not (shape.get("labels_present") or shape.get("observation_label_count") or shape.get("reception_label_count")):
        return reasons
    if not shape.get("labels_present"):
        reasons.extend(["two_stage_labels_missing_or_duplicated", "two_stage_label_missing"])
    if shape.get("labels_present") and not shape.get("label_order_valid"):
        reasons.extend(["two_stage_label_order_invalid", "two_stage_section_order_invalid"])
    if shape.get("label_order_valid") and not shape.get("observation_section_non_empty"):
        reasons.append("two_stage_observation_section_empty")
    if shape.get("label_order_valid") and not shape.get("reception_section_non_empty"):
        reasons.append("two_stage_reception_section_empty")
    return reasons


def _boundary_reasons(observation: str, reception: str) -> list[str]:
    reasons: list[str] = []
    if _OBSERVATION_COMMENT_TONE_RE.search(observation):
        reasons.extend(["observation_section_comment_tone_leak", "two_stage_observation_section_contains_human_follow"])
    if _RECEPTION_NEW_FACT_OVERCLAIM_RE.search(reception):
        reasons.append("reception_section_new_fact_overclaim")
    if _DIAGNOSIS_RE.search(reception):
        reasons.append("reception_section_diagnosis_surface")
    if _PERSONALITY_CLAIM_RE.search(reception):
        reasons.append("reception_section_personality_claim_surface")
    if _ACTION_INSTRUCTION_RE.search(reception):
        reasons.append("reception_section_action_instruction_surface")
    if _STABLE_GROWTH_OR_RECOVERY_ASSERTION_RE.search(reception) or _STABLE_GROWTH_OR_RECOVERY_ASSERTION_RE.search(observation):
        reasons.extend([
            "reception_section_stable_growth_or_recovery_assertion",
            "reception_section_stable_state_overclaim",
        ])
    return reasons


def _consistency_reasons(*, full_surface: str, reception: str, shared_evidence: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    reaction_present = bool(shared_evidence.get("reaction_present"))
    event_hint_ids = _dedupe(shared_evidence.get("event_hint_ids") or [])
    general_dictionary_used = bool(shared_evidence.get("general_dictionary_used"))
    unknown_meaning_asserted = bool(shared_evidence.get("unknown_word_meaning_asserted"))
    if _TARGET_JUDGEMENT_AGREEMENT_RE.search(full_surface):
        reasons.extend(["target_judgement_agreement", "two_stage_target_judgement_agreement_surface"])
    if _EVENT_HINT_RISK_OVERCLAIM_RE.search(reception):
        reasons.extend(["event_hint_created_emotion", "two_stage_event_hint_created_emotion_surface"])
    elif event_hint_ids and not reaction_present and _EVENT_HINT_EMOTION_OVERCLAIM_RE.search(reception):
        reasons.extend(["event_hint_created_emotion", "two_stage_event_hint_created_emotion_surface"])
    if _UNKNOWN_WORD_ASSERTION_RE.search(full_surface) or unknown_meaning_asserted or general_dictionary_used:
        reasons.append("unknown_word_meaning_asserted")
    return reasons


def _mode_specific_reasons(*, full_surface: str, observation: str, reception: str, mode_id: str, shared_evidence: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    mode_family = _mode_family(mode_id)
    event_fact_present = bool(shared_evidence.get("event_fact_present"))
    if mode_family == "daily_reception":
        if event_fact_present and _QUESTION_ESCAPE_RE.search(full_surface):
            reasons.extend(["daily_reception_question_escape_when_event_fact_present", "two_stage_daily_reception_low_information_question_escape"])
        if _section_sentence_count(observation) > 2 or _section_sentence_count(reception) > 3:
            reasons.append("daily_reception_over_explained")
        if _ANALYTIC_OVER_EXPLAIN_RE.search(observation) or _ANALYTIC_OVER_EXPLAIN_RE.search(reception):
            reasons.append("daily_reception_analytic_over_explained")
    if mode_family == "self_negative_or_uncertainty":
        if re.search(r"(?:中途半端な人ではありません|本当はすごい人|自信を持ちましょう)", full_surface):
            reasons.append("self_denial_identity_claim_as_fact")
    return reasons


def _koto_splice_codes(full_surface: str) -> list[str]:
    patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("malformed_nominalization_conditional_fragment", re.compile(r"(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|取らなければ)こと(?:$|[もがはにをでへ、。,.])")),
        ("malformed_nominalization_prediction_noun_fragment", re.compile(r"(?:予感|気配|予定|必要|つもり|はず|可能性|見込み|感じ)こと(?:$|[もがはにをでへ、。,.])")),
        ("malformed_nominalization_adjective_fragment", re.compile(r"(?:得意|好き|嫌い|中途半端|大丈夫|平気)こと(?:$|[もがはにをでへ、。,.])")),
        ("malformed_nominalization_feeling_transition_fragment", re.compile(r"(?:気持ちになって|気持ちになり|頑張りたいって気持ちになって)こと")),
    )
    return _dedupe(code for code, pattern in patterns if pattern.search(full_surface))


def _surface_quality_reasons(full_surface: str) -> list[str]:
    reasons: list[str] = []
    if any(pattern.search(full_surface) for pattern in _MALFORMED_NOMINALIZATION_PATTERNS) or _koto_splice_codes(full_surface):
        reasons.extend([
            "two_stage_koto_splice_or_malformed_nominalization",
            "two_stage_bad_grammar_or_koto_splice_surface",
        ])
    if _INTERNAL_ROLE_LABEL_LEAK_RE.search(full_surface):
        reasons.extend([
            "two_stage_internal_role_label_leak",
            "two_stage_complete_surface_internal_label_leak",
        ])
    if _RELATION_SKELETON_RE.search(full_surface):
        reasons.extend(["two_stage_relation_skeleton_leak", "two_stage_relation_skeleton_leak_surface"])
    if _TEMPLATE_ECHO_RE.search(full_surface):
        reasons.append("two_stage_template_echo_loop")
    return reasons






def _complete_surface_meta_from_composer_meta(composer_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _as_mapping(composer_meta)
    direct = _as_mapping(meta.get("two_stage_surface_realization"))
    if direct:
        return _deepcopy_mapping(direct)
    surface_realizer = _as_mapping(meta.get("surface_realizer"))
    nested = _as_mapping(surface_realizer.get("two_stage_surface_realization"))
    if nested:
        return _deepcopy_mapping(nested)
    return {}


def _complete_sentence_plan_meta_from_composer_meta(composer_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _as_mapping(composer_meta)
    direct = _as_mapping(meta.get("sentence_plan"))
    if direct:
        return _deepcopy_mapping(direct)
    surface_realizer = _as_mapping(meta.get("surface_realizer"))
    source_plan_summary = _as_mapping(surface_realizer.get("source_plan_summary"))
    if source_plan_summary:
        return _deepcopy_mapping(source_plan_summary)
    return {}


def _complete_surface_diagnostic_reasons(
    *,
    shape: Mapping[str, Any],
    two_stage_required: bool,
    composer_meta: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return Phase16-7 Complete-specific reason aliases.

    These codes identify why a required two-stage visible surface cannot be
    shown. They are meta-only diagnostics: no section bodies, raw input, memo,
    or candidate text is returned.
    """

    if not two_stage_required:
        return []

    reasons: list[str] = []
    surface_meta = _complete_surface_meta_from_composer_meta(composer_meta)
    sentence_plan_meta = _complete_sentence_plan_meta_from_composer_meta(composer_meta)
    validation_errors = _dedupe(surface_meta.get("validation_errors") or [])

    labels_present = bool(shape.get("labels_present"))
    label_order_valid = bool(shape.get("label_order_valid"))
    observation_non_empty = bool(shape.get("observation_section_non_empty"))
    reception_non_empty = bool(shape.get("reception_section_non_empty"))

    if not labels_present:
        reasons.extend([
            "two_stage_required_but_unrealized",
            "two_stage_complete_surface_realizer_label_missing",
        ])
    if labels_present and label_order_valid and (not observation_non_empty or not reception_non_empty):
        reasons.extend([
            "two_stage_required_but_unrealized",
            "two_stage_complete_surface_realizer_section_empty",
        ])

    if surface_meta:
        if surface_meta.get("applied") is False:
            reasons.append("two_stage_required_but_unrealized")
        if surface_meta.get("labels_present") is False:
            reasons.append("two_stage_complete_surface_realizer_label_missing")
        if (
            surface_meta.get("observation_section_non_empty") is False
            or surface_meta.get("reception_section_non_empty") is False
        ):
            reasons.append("two_stage_complete_surface_realizer_section_empty")

    missing_observation = (
        "two_stage_complete_sentence_plan_observation_section_missing" in validation_errors
        or surface_meta.get("observation_section_present") is False
    )
    missing_reception = (
        "two_stage_complete_sentence_plan_reception_section_missing" in validation_errors
        or surface_meta.get("reception_section_present") is False
    )
    if missing_observation:
        reasons.append("two_stage_complete_sentence_plan_observation_section_missing")
    if missing_reception:
        reasons.append("two_stage_complete_sentence_plan_reception_section_missing")
    if missing_observation or missing_reception:
        reasons.append("two_stage_complete_sentence_plan_section_meta_missing")

    if sentence_plan_meta:
        section_ids = _dedupe(
            sentence_plan_meta.get("two_stage_section_ids")
            or sentence_plan_meta.get("two_stage_section_surface_plan_section_ids")
            or []
        )
        if section_ids and ("observation" not in section_ids or "reception" not in section_ids):
            reasons.append("two_stage_complete_sentence_plan_section_meta_missing")
        section_summary = _as_mapping(sentence_plan_meta.get("two_stage_section_summary"))
        summary_ids = _dedupe(section_summary.get("section_ids") or [])
        if summary_ids and ("observation" not in summary_ids or "reception" not in summary_ids):
            reasons.append("two_stage_complete_sentence_plan_section_meta_missing")

    for reason in validation_errors:
        if reason.startswith("two_stage_"):
            reasons.append(reason)

    reasons = _dedupe(reasons)
    if reasons:
        reasons.append("two_stage_complete_surface_blocked_by_gate")
    return _dedupe(reasons)


def _two_stage_applicability_from_inputs(
    *,
    full_surface: str,
    shape: Mapping[str, Any],
    composer_meta: Mapping[str, Any] | None = None,
    explicit_required: bool | None = None,
) -> dict[str, Any]:
    meta = _as_mapping(composer_meta)
    surface_meta = _as_mapping(meta.get("two_stage_surface_realization"))
    if not surface_meta:
        surface_meta = _as_mapping(_complete_surface_meta_from_composer_meta(meta))
    return build_two_stage_applicability_decision(
        composer_meta=meta,
        candidate_source=meta.get("composer_source", ""),
        candidate_status=meta.get("status") or meta.get("candidate_status") or "",
        comment_text_present=bool(_clean(full_surface)),
        surface_shape=shape,
        state_answer_two_stage_meta=meta,
        two_stage_section_plan_meta=meta.get("two_stage_section_surface_plan") if isinstance(meta.get("two_stage_section_surface_plan"), Mapping) else meta,
        two_stage_surface_meta=surface_meta,
        branch_kind=meta.get("observation_reply_kind") or meta.get("eligibility_status") or meta.get("generation_scope") or "",
        explicit_required=explicit_required,
    )


def _two_stage_applicability_decision_from_inputs(
    *,
    full_surface: str,
    shape: Mapping[str, Any],
    composer_meta: Mapping[str, Any] | None = None,
    state_answer_surface_contract: Any = None,
    two_stage_required: bool | None = None,
) -> dict[str, Any]:
    meta = _as_mapping(composer_meta)
    contract = _as_mapping(state_answer_surface_contract)
    section_plan = _as_mapping(meta.get("two_stage_section_surface_plan"))
    return build_two_stage_applicability_decision(
        composer_meta=meta,
        state_answer_surface_contract=contract,
        two_stage_section_surface_plan=section_plan,
        candidate_source=meta.get("composer_source", ""),
        candidate_status=meta.get("candidate_status") or meta.get("status") or meta.get("complete_initial_candidate_status") or "",
        comment_text_present=bool(_clean(full_surface)),
        labels_present=bool(shape.get("labels_present")),
        explicit_required=two_stage_required,
    )


def _two_stage_required_from_inputs(*, full_surface: str, shape: Mapping[str, Any], composer_meta: Mapping[str, Any] | None = None) -> bool:
    decision = _two_stage_applicability_decision_from_inputs(
        full_surface=full_surface,
        shape=shape,
        composer_meta=composer_meta,
    )
    return bool(decision.get("required"))

def _composer_requires_two_stage(composer_meta: Mapping[str, Any] | None) -> bool:
    meta = _as_mapping(composer_meta)
    containers = [meta]
    for container_key in ("composition_contract", "state_answer_composer_role_plan", "composer_payload", "payload", "diagnostic_summary"):
        container = _as_mapping(meta.get(container_key))
        if container:
            containers.append(container)
            nested = _as_mapping(container.get("composition_contract"))
            if nested:
                containers.append(nested)
            nested_role = _as_mapping(container.get("state_answer_composer_role_plan"))
            if nested_role:
                containers.append(nested_role)
    for container in containers:
        if (
            container.get("two_stage_display_required")
            or container.get("section_labels_required")
            or container.get("joined_comment_text_required")
            or container.get("two_stage_reception_surface_required")
            or container.get("expected_comment_text_shape") == "labelled_two_stage_text"
        ):
            return True
    return False


def build_two_stage_reception_gate_report(*, comment_text: Any = "", visible_surface: Any = None, state_answer_surface_contract: Any = None, composer_meta: Mapping[str, Any] | None = None, shared_reception_evidence: Any = None, reception_mode: Any = None, current_input: Any = None, two_stage_required: bool | None = None) -> dict[str, Any]:
    """Evaluate a two-stage reception surface and return a meta-only report."""
    full_surface = str(comment_text if visible_surface is None else visible_surface or "")
    contract = _contract_from_inputs(state_answer_surface_contract=state_answer_surface_contract, composer_meta=composer_meta)
    evidence = _merge_evidence(
        _shared_evidence_from_inputs(
            shared_reception_evidence=shared_reception_evidence,
            state_answer_surface_contract=contract,
            composer_meta=composer_meta,
        ),
        _current_input_evidence(current_input),
    )
    mode_id = _mode_id_from_inputs(reception_mode=reception_mode, state_answer_surface_contract=contract, composer_meta=composer_meta)
    shape = _split_sections(full_surface)
    applicability_decision = _two_stage_applicability_from_inputs(
        full_surface=full_surface,
        shape=shape,
        composer_meta=composer_meta,
        explicit_required=two_stage_required,
    )
    required = bool(applicability_decision.get("required"))
    observation = str(shape.pop("observation_section") or "")
    reception = str(shape.pop("reception_section") or "")
    evaluated = bool(required or shape.get("labels_present") or shape.get("observation_label_count") or shape.get("reception_label_count"))
    section_shape_reasons = _section_shape_reasons(shape, two_stage_required=required) if evaluated else []
    boundary_reasons = _boundary_reasons(observation, reception) if evaluated and shape.get("label_order_valid") else []
    consistency_reasons = (
        _consistency_reasons(full_surface=full_surface, reception=reception, shared_evidence=evidence)
        if evaluated
        else []
    )
    mode_specific_reasons = (
        _mode_specific_reasons(full_surface=full_surface, observation=observation, reception=reception, mode_id=mode_id, shared_evidence=evidence)
        if evaluated
        else []
    )
    surface_quality_reasons = _surface_quality_reasons(full_surface) if evaluated else []
    complete_surface_diagnostic_reasons = (
        _complete_surface_diagnostic_reasons(
            shape=shape,
            two_stage_required=required,
            composer_meta=composer_meta,
        )
        if evaluated
        else []
    )
    reasons = _dedupe([
        *section_shape_reasons,
        *boundary_reasons,
        *consistency_reasons,
        *mode_specific_reasons,
        *surface_quality_reasons,
        *complete_surface_diagnostic_reasons,
    ])
    passed = bool((not evaluated) or not reasons)
    report = {
        "schema_version": EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION,
        "version": EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION,
        "material_id": EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID,
        "source_phase": EMLIS_AI_TWO_STAGE_RECEPTION_GATE_PHASE,
        "phase": EMLIS_AI_TWO_STAGE_RECEPTION_GATE_PHASE,
        "connected": bool(evaluated),
        "evaluated": bool(evaluated),
        "active": bool(evaluated),
        "two_stage_required": bool(required),
        "two_stage_applicability_decision": applicability_decision,
        "two_stage_applicability_required": bool(applicability_decision.get("required")),
        "two_stage_applicability_decision_reason": _clean(applicability_decision.get("decision_reason")),
        "two_stage_applicability_exempt": bool(applicability_decision.get("exempt")),
        "two_stage_applicability_exemption_reason": _clean(applicability_decision.get("exemption_reason")),
        "passed": passed,
        "blocked": bool(evaluated and reasons),
        "terminal_surface_block": bool(evaluated and reasons),
        "rejection_reasons": reasons,
        "surface_blocker_reasons": reasons,
        "section_shape_rejection_reasons": section_shape_reasons,
        "section_boundary_rejection_reasons": boundary_reasons,
        "consistency_rejection_reasons": consistency_reasons,
        "mode_specific_rejection_reasons": mode_specific_reasons,
        "surface_quality_rejection_reasons": surface_quality_reasons,
        "complete_surface_diagnostic_reasons": complete_surface_diagnostic_reasons,
        "complete_surface_rejection_reasons": complete_surface_diagnostic_reasons,
        "phase16_7_unavailable_reason_codes": complete_surface_diagnostic_reasons,
        "two_stage_unavailable_reason_codes": complete_surface_diagnostic_reasons,
        "two_stage_required_but_unrealized": "two_stage_required_but_unrealized" in reasons,
        "two_stage_complete_surface_realizer_label_missing": "two_stage_complete_surface_realizer_label_missing" in reasons,
        "two_stage_complete_surface_realizer_section_empty": "two_stage_complete_surface_realizer_section_empty" in reasons,
        "two_stage_complete_sentence_plan_section_meta_missing": "two_stage_complete_sentence_plan_section_meta_missing" in reasons,
        "two_stage_complete_sentence_plan_observation_section_missing": "two_stage_complete_sentence_plan_observation_section_missing" in reasons,
        "two_stage_complete_sentence_plan_reception_section_missing": "two_stage_complete_sentence_plan_reception_section_missing" in reasons,
        "two_stage_complete_surface_blocked_by_gate": "two_stage_complete_surface_blocked_by_gate" in reasons,
        "labels_present": bool(shape.get("labels_present")),
        "two_stage_labels_present": bool(shape.get("labels_present")),
        "section_order_valid": bool(shape.get("label_order_valid")),
        "label_order_valid": bool(shape.get("label_order_valid")),
        "observation_label_present": int(shape.get("observation_label_count") or 0) == 1,
        "reception_label_present": int(shape.get("reception_label_count") or 0) == 1,
        "observation_section_non_empty": bool(shape.get("observation_section_non_empty")),
        "observation_section_present": bool(shape.get("observation_section_non_empty")),
        "reception_section_non_empty": bool(shape.get("reception_section_non_empty")),
        "reception_section_present": bool(shape.get("reception_section_non_empty")),
        "observation_label_count": int(shape.get("observation_label_count") or 0),
        "reception_label_count": int(shape.get("reception_label_count") or 0),
        "observation_section_sentence_count": _section_sentence_count(observation) if shape.get("label_order_valid") else 0,
        "reception_section_sentence_count": _section_sentence_count(reception) if shape.get("label_order_valid") else 0,
        "reception_mode_id": mode_id,
        "reception_mode_family": _mode_family(mode_id),
        "event_fact_present": bool(evidence.get("event_fact_present")),
        "reaction_present": bool(evidence.get("reaction_present")),
        "event_hint_ids": _dedupe(evidence.get("event_hint_ids") or []),
        "target_judgement_agreement_blocked": "target_judgement_agreement" in reasons,
        "daily_reception_question_escape_blocked": "daily_reception_question_escape_when_event_fact_present" in reasons,
        "daily_reception_low_information_question_escape_blocked": "daily_reception_question_escape_when_event_fact_present" in reasons,
        "event_hint_emotion_fabrication_blocked": "event_hint_created_emotion" in reasons,
        "koto_splice_or_malformed_nominalization_blocked": "two_stage_koto_splice_or_malformed_nominalization" in reasons,
        "bad_grammar_or_koto_splice_blocked": "two_stage_bad_grammar_or_koto_splice_surface" in reasons,
        "koto_splice_detected": "two_stage_bad_grammar_or_koto_splice_surface" in reasons,
        "koto_splice_codes": _koto_splice_codes(full_surface),
        "internal_role_label_leak_blocked": "two_stage_internal_role_label_leak" in reasons,
        "complete_surface_internal_label_leak_blocked": "two_stage_complete_surface_internal_label_leak" in reasons,
        "relation_skeleton_leak_blocked": "two_stage_relation_skeleton_leak" in reasons,
        "observation_reception_mixing_blocked": "observation_section_comment_tone_leak" in reasons,
        "public_meta_summary_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "observation_text_included": False,
        "reception_text_included": False,
        "section_body_included": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "gate_relaxed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
    }
    assert_two_stage_reception_gate_contract(report)
    return report


def two_stage_reception_gate_public_summary(value: Any) -> dict[str, Any]:
    source = _as_mapping(value)
    if not source:
        return {}
    if _source_has_unsafe_flags(source):
        return {"evaluated": True, "passed": False, "blocked": True, "terminal_surface_block": True, "rejection_reasons": ["two_stage_reception_gate_public_meta_unsafe"], "public_meta_summary_only": True}
    summary: dict[str, Any] = {}
    for key in (
        "evaluated", "active", "connected", "two_stage_required", "two_stage_applicability_required", "two_stage_applicability_exempt", "passed", "blocked", "terminal_surface_block", "labels_present", "two_stage_labels_present", "observation_label_present", "reception_label_present", "label_order_valid",
        "observation_section_non_empty", "reception_section_non_empty", "target_judgement_agreement_blocked",
        "daily_reception_question_escape_blocked", "daily_reception_low_information_question_escape_blocked",
        "event_hint_emotion_fabrication_blocked", "koto_splice_or_malformed_nominalization_blocked",
        "bad_grammar_or_koto_splice_blocked", "koto_splice_detected",
        "internal_role_label_leak_blocked", "complete_surface_internal_label_leak_blocked",
        "relation_skeleton_leak_blocked", "observation_reception_mixing_blocked", "two_stage_required_but_unrealized",
        "two_stage_complete_surface_realizer_label_missing", "two_stage_complete_surface_realizer_section_empty",
        "two_stage_complete_sentence_plan_section_meta_missing",
        "two_stage_complete_sentence_plan_observation_section_missing",
        "two_stage_complete_sentence_plan_reception_section_missing",
        "two_stage_complete_surface_blocked_by_gate", "public_meta_summary_only",
    ):
        if isinstance(source.get(key), bool):
            summary[key] = bool(source.get(key))
    for key in (
        "rejection_reasons", "surface_blocker_reasons", "section_shape_rejection_reasons", "section_boundary_rejection_reasons",
        "consistency_rejection_reasons", "mode_specific_rejection_reasons", "surface_quality_rejection_reasons",
        "complete_surface_diagnostic_reasons", "complete_surface_rejection_reasons",
        "phase16_7_unavailable_reason_codes", "two_stage_unavailable_reason_codes", "koto_splice_codes",
    ):
        reasons = _dedupe(source.get(key) or [])
        if reasons:
            summary[key] = reasons[:12]
    decision = _as_mapping(source.get("two_stage_applicability_decision"))
    if decision:
        summary["two_stage_applicability_decision"] = {
            key: decision[key]
            for key in (
                "schema_version",
                "source_phase",
                "required",
                "decision_reason",
                "candidate_source",
                "candidate_status",
                "comment_text_present",
                "section_plan_connected",
                "state_answer_contract_required",
                "exempt",
                "exemption_reason",
                "terminal_when_label_missing",
            )
            if key in decision
        }
    for key in ("reception_mode_id", "reception_mode_family", "two_stage_applicability_decision_reason", "two_stage_applicability_exemption_reason"):
        value_text = _clean(source.get(key))
        if value_text:
            summary[key] = value_text
    codes = _dedupe(source.get("koto_splice_codes") or [])
    if codes:
        summary["koto_splice_codes"] = codes[:12]
    if "observation_section_sentence_count" in source:
        summary["observation_section_sentence_count"] = int(source.get("observation_section_sentence_count") or 0)
    if "reception_section_sentence_count" in source:
        summary["reception_section_sentence_count"] = int(source.get("reception_section_sentence_count") or 0)
    if summary:
        summary["public_meta_summary_only"] = True
    assert_two_stage_reception_gate_contract(summary, source="two_stage_reception_gate_public_summary")
    return summary


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


def _source_has_unsafe_flags(value: Mapping[str, Any]) -> bool:
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            return True
    return False


def assert_two_stage_reception_gate_contract(value: Any, *, source: str = "two_stage_reception_gate") -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment/section/evidence payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates public boundary contract: {key}=true")
    schema = _clean(value.get("schema_version"))
    if schema and schema != EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION:
        raise ValueError(f"{source} has unexpected schema_version")
    material_id = _clean(value.get("material_id"))
    if material_id and material_id != EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID:
        raise ValueError(f"{source} has unexpected material_id")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc



build_emlis_ai_two_stage_reception_gate_report = build_two_stage_reception_gate_report
build_emlis_two_stage_reception_gate_report = build_two_stage_reception_gate_report
assert_emlis_ai_two_stage_reception_gate_contract = assert_two_stage_reception_gate_contract
assert_emlis_two_stage_reception_gate_contract = assert_two_stage_reception_gate_contract
emlis_ai_two_stage_reception_gate_public_summary = two_stage_reception_gate_public_summary
emlis_two_stage_reception_gate_public_summary = two_stage_reception_gate_public_summary

__all__ = [
    "EMLIS_AI_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION",
    "EMLIS_TWO_STAGE_RECEPTION_GATE_SCHEMA_VERSION",
    "EMLIS_AI_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID",
    "EMLIS_TWO_STAGE_RECEPTION_GATE_MATERIAL_ID",
    "EMLIS_AI_TWO_STAGE_RECEPTION_GATE_PHASE",
    "EMLIS_TWO_STAGE_RECEPTION_GATE_PHASE",
    "OBSERVATION_LABEL",
    "RECEPTION_LABEL",
    "build_two_stage_reception_gate_report",
    "build_emlis_ai_two_stage_reception_gate_report",
    "build_emlis_two_stage_reception_gate_report",
    "two_stage_reception_gate_public_summary",
    "emlis_ai_two_stage_reception_gate_public_summary",
    "emlis_two_stage_reception_gate_public_summary",
    "assert_two_stage_reception_gate_contract",
    "assert_emlis_ai_two_stage_reception_gate_contract",
    "assert_emlis_two_stage_reception_gate_contract",
]
