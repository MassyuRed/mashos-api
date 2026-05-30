# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 8 Gate / Public Meta boundary for EmlisAI state answers.

This module is a meta-only guard.  It evaluates a candidate visible surface in
memory against the state-answer surface contract and returns only small reason
codes and booleans.  It never returns the candidate body, raw input, raw
evidence, memo, memo_action, or comment_text.
"""

from collections.abc import Iterable, Mapping
import copy
import json
import re
from typing import Any, Final

from emlis_ai_state_answer_special_cases import (
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
    state_answer_special_cases_forward_meta,
    state_answer_special_cases_surface_gate_check,
)
from emlis_ai_two_stage_reception_gate import (
    build_two_stage_reception_gate_report,
    two_stage_reception_gate_public_summary,
)

EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis_ai_state_answer.gate_public_meta_boundary.v1"
)
EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_MATERIAL_ID: Final = (
    "emlis_ai_state_answer_gate_public_meta_boundary"
)
EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_PHASE: Final = "Phase8_gate_public_meta_boundary"

_SPACE_RE: Final = re.compile(r"\s+")

# Guard classifiers only.  They are never used as runtime reply templates.
_DIAGNOSIS_RE: Final = re.compile(
    r"(?:診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|PTSD|医学的|心理学的)"
)
_ACTION_INSTRUCTION_RE: Final = re.compile(
    r"(?:してください|しましょう|するべき|しなければ|行動しましょう|連絡しましょう|決めましょう|距離を取(?:った|り)方がいい|休みましょう|相談しましょう)"
)
_PERSONALITY_CLAIM_RE: Final = re.compile(
    r"(?:あなたは(?:こういう人|優しい人|素晴らしい人|弱い人ではありません|本当は強い|本質的に|性格的に|依存している|ダメな人|駄目な人)|性格だから|本質は[^。！？!?\n]{0,20}です)"
)
_ABSOLUTE_SUPPORT_RE: Final = re.compile(
    r"(?:何があっても味方|絶対(?:に)?味方|全部受け止めます|必ず(?:良く|よく)なります|絶対(?:に)?悪くありません|もう大丈夫|安心してください)"
)
_CAUSE_OVERCLAIM_RE: Final = re.compile(
    r"(?:原因はこれです|原因は[^。！？!?\n]{0,16}です|本当の原因|理由はひとつ|カテゴリが原因|感情の強さが原因)"
)
_PERIOD_TENDENCY_RE: Final = re.compile(
    r"(?:いつも|毎回|ずっと|長い間|繰り返し)[^。！？!?\n]{0,24}(?:そう|同じ|傾向|性格)"
)
_OVER_CLOSE_RE: Final = re.compile(
    r"(?:ずっとそばに|抱きしめ|一緒なら大丈夫|泣いていい|全部わかります|全部わかる)"
)
_ANGER_TARGET_JUDGEMENT_RE: Final = re.compile(
    r"(?:(?:相手|上司|あの人|その人|彼|彼女|会社|職場)[^。！？!?\n]{0,24}(?:悪い|ひどい|最低|おかしい|間違って|軽く見て|見下して|敵)|あなたの怒りは(?:正しい|当然)|相手が悪い|上司が悪い)"
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
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "surface_text",
        "realized_text",
        "evidence_text",
        "raw_quote",
        "raw_quotes",
        "body",
        "text",
        "sentence",
        "sentences",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "state_answer_contract_body_in_public_meta",
        "state_answer_raw_evidence_in_public_meta",
        "state_answer_comment_text_body_in_public_meta",
        "observation_text_public_key_added",
        "reception_text_public_key_added",
        "public_response_key_added",
        "public_response_key_change",
        "response_shape_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "gate_relaxed",
        "external_ai_used",
        "local_llm_used",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
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


def _pick_state_answer_surface_contract(
    *,
    state_answer_surface_contract: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    direct = _as_mapping(state_answer_surface_contract)
    if direct:
        return copy.deepcopy(dict(direct))
    meta = _as_mapping(composer_meta)
    for key in (
        "state_answer_surface_contract",
        "emlis_state_answer_surface_contract",
        "state_answer_contract",
    ):
        found = _as_mapping(meta.get(key))
        if found:
            return copy.deepcopy(dict(found))
    for container_key in ("composer_meta", "composition_contract", "diagnostic_summary", "gate_trace"):
        container = _as_mapping(meta.get(container_key))
        for key in (
            "state_answer_surface_contract",
            "emlis_state_answer_surface_contract",
            "state_answer_contract",
        ):
            found = _as_mapping(container.get(key))
            if found:
                return copy.deepcopy(dict(found))
    return {}


def _pick_special_cases(
    *,
    state_answer_special_cases: Any = None,
    state_answer_surface_contract: Mapping[str, Any] | None = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    direct = state_answer_special_cases_forward_meta(state_answer_special_cases)
    if direct:
        return direct
    contract = _as_mapping(state_answer_surface_contract)
    for key in (
        "special_handling",
        "state_answer_special_cases",
        "state_answer_special_cases_payload",
    ):
        found = state_answer_special_cases_forward_meta(contract.get(key))
        if found:
            return found
    meta = _as_mapping(composer_meta)
    for key in (
        "state_answer_special_cases",
        "state_answer_special_cases_payload",
        "special_handling",
    ):
        found = state_answer_special_cases_forward_meta(meta.get(key))
        if found:
            return found
    nested_contract = _pick_state_answer_surface_contract(
        state_answer_surface_contract=None,
        composer_meta=meta,
    )
    if nested_contract:
        return _pick_special_cases(state_answer_surface_contract=nested_contract)
    return {}


def _forbidden_claim_reasons(surface: str) -> list[str]:
    reasons: list[str] = []
    if _DIAGNOSIS_RE.search(surface):
        reasons.append("state_answer_diagnosis_surface")
    if _ACTION_INSTRUCTION_RE.search(surface):
        reasons.append("state_answer_action_instruction_surface")
    if _PERSONALITY_CLAIM_RE.search(surface):
        reasons.append("state_answer_personality_claim_surface")
    if _ABSOLUTE_SUPPORT_RE.search(surface):
        reasons.append("state_answer_absolute_support_or_alliance_surface")
    if _OVER_CLOSE_RE.search(surface):
        reasons.append("state_answer_over_close_support_surface")
    if _CAUSE_OVERCLAIM_RE.search(surface):
        reasons.append("state_answer_cause_or_reason_overclaim_surface")
    if _PERIOD_TENDENCY_RE.search(surface):
        reasons.append("state_answer_period_tendency_from_single_record_surface")
    if _ANGER_TARGET_JUDGEMENT_RE.search(surface):
        reasons.append("anger_target_judgement_agreement")
    return _dedupe(reasons)


def build_state_answer_gate_boundary_report(
    *,
    visible_surface: Any = "",
    state_answer_surface_contract: Any = None,
    state_answer_special_cases: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
    current_input: Any = None,
    two_stage_reception_gate_required: bool = False,
    shared_reception_evidence: Any = None,
    reception_mode: Any = None,
) -> dict[str, Any]:
    """Evaluate Phase 8 state-answer Gate/Public Meta boundary.

    The visible surface is inspected only in memory.  The returned mapping is
    safe to forward as nested gate meta; it carries reason codes only.
    """

    contract = _pick_state_answer_surface_contract(
        state_answer_surface_contract=state_answer_surface_contract,
        composer_meta=composer_meta,
    )
    special_cases = _pick_special_cases(
        state_answer_special_cases=state_answer_special_cases,
        state_answer_surface_contract=contract,
        composer_meta=composer_meta,
    )
    surface = _clean(visible_surface)
    # Phase16-1: a required two-stage surface must be blocked even before the
    # labels appear in the body.  Passing ``None`` lets the two-stage gate derive
    # the requirement from composer_meta / contract and report label-missing
    # reasons instead of silently staying inactive.
    two_stage_required_override = True if two_stage_reception_gate_required else None
    special_case_report = state_answer_special_cases_surface_gate_check(
        visible_surface=surface,
        special_cases=special_cases,
        current_input=current_input,
    )
    two_stage_reception_gate_report = build_two_stage_reception_gate_report(
        visible_surface=surface,
        state_answer_surface_contract=contract,
        composer_meta=composer_meta,
        current_input=current_input,
        shared_reception_evidence=shared_reception_evidence,
        reception_mode=reception_mode,
        two_stage_required=two_stage_required_override,
    )

    two_stage_reception_gate_active = bool(two_stage_reception_gate_report.get("evaluated"))
    gate_context_active = bool(contract or special_cases or two_stage_reception_gate_active)
    generic_reasons = _forbidden_claim_reasons(surface) if gate_context_active else []
    special_case_reasons = _dedupe(special_case_report.get("surface_blocker_reasons") or []) if gate_context_active else []
    two_stage_reception_gate_reasons = (
        _dedupe(
            two_stage_reception_gate_report.get("surface_blocker_reasons")
            or two_stage_reception_gate_report.get("rejection_reasons")
            or []
        )
        if two_stage_reception_gate_active
        else []
    )
    two_stage_unavailable_reason_codes = _dedupe(
        two_stage_reception_gate_report.get("two_stage_unavailable_reason_codes")
        or two_stage_reception_gate_report.get("phase16_7_unavailable_reason_codes")
        or []
    )
    allowed_exception_ids = _dedupe(special_case_report.get("allowed_exception_ids_detected") or [])
    warning_reasons = _dedupe(special_case_report.get("surface_warning_reasons") or [])

    self_denial_enabled = bool(
        special_case_report.get("self_denial_special_handling_enabled")
        or _as_mapping(special_cases.get("self_denial")).get("enabled")
    )
    anger_enabled = bool(
        special_case_report.get("anger_special_handling_enabled")
        or _as_mapping(special_cases.get("anger")).get("enabled")
    )
    counter_allowed = bool(special_case_report.get("self_denial_limited_counter_opinion_allowed"))
    counter_evidence_ready = bool(special_case_report.get("self_denial_exception_evidence_ready"))
    if counter_allowed and not counter_evidence_ready:
        generic_reasons.append("self_denial_counter_opinion_without_input_evidence")

    reasons = _dedupe([*generic_reasons, *special_case_reasons, *two_stage_reception_gate_reasons])
    passed = not reasons
    report = {
        "schema_version": EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION,
        "version": EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION,
        "material_id": EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_MATERIAL_ID,
        "source_phase": EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_PHASE,
        "phase": EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_PHASE,
        "evaluated": True,
        "passed": bool(passed),
        "blocked": not bool(passed),
        "terminal_surface_block": bool(reasons),
        "rejection_reasons": reasons,
        "surface_blocker_reasons": reasons,
        "forbidden_claim_reasons": _dedupe(generic_reasons),
        "special_case_rejection_reasons": special_case_reasons,
        "two_stage_reception_gate": two_stage_reception_gate_public_summary(two_stage_reception_gate_report),
        "two_stage_reception_gate_rejection_reasons": two_stage_reception_gate_reasons,
        "phase16_7_unavailable_reason_codes": list(two_stage_unavailable_reason_codes),
        "two_stage_unavailable_reason_codes": list(two_stage_unavailable_reason_codes),
        "two_stage_required_but_unrealized": "two_stage_required_but_unrealized" in two_stage_reception_gate_reasons,
        "two_stage_complete_surface_blocked_by_gate": bool(
            "two_stage_complete_surface_blocked_by_gate" in two_stage_reception_gate_reasons
        ),
        "two_stage_reception_gate_connected": bool(two_stage_reception_gate_report.get("connected")),
        "two_stage_reception_gate_terminal_surface_block": bool(
            two_stage_reception_gate_report.get("terminal_surface_block")
            or two_stage_reception_gate_reasons
        ),
        "two_stage_reception_gate_evaluated": bool(two_stage_reception_gate_report.get("evaluated")),
        "two_stage_reception_gate_passed": bool(two_stage_reception_gate_report.get("passed")),
        "two_stage_reception_cross_gate_connected": bool(two_stage_reception_gate_report.get("connected")),
        "two_stage_reception_cross_gate_active": bool(two_stage_reception_gate_active),
        "warning_reasons": warning_reasons,
        "allowed_exception_ids": allowed_exception_ids,
        "allowed_exception_ids_detected": allowed_exception_ids,
        "state_answer_gate_boundary_connected": bool(gate_context_active),
        "state_answer_surface_contract_connected": bool(contract),
        "state_answer_surface_contract_material_id": _clean(contract.get("material_id")),
        "state_answer_special_cases_connected": bool(special_cases),
        "state_answer_special_cases_material_id": _clean(
            special_cases.get("material_id") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID if special_cases else ""
        ),
        "self_denial_special_handling_enabled": self_denial_enabled,
        "self_denial_limited_counter_opinion_allowed": counter_allowed,
        "self_denial_exception_evidence_ready": counter_evidence_ready,
        "anger_special_handling_enabled": anger_enabled,
        "anger_target_judgement_agreement_blocked": (
            "anger_target_judgement_agreement" in reasons
            or "target_judgement_agreement" in reasons
            or "two_stage_target_judgement_agreement" in reasons
        ),
        "anger_target_attack_amplification_blocked": "anger_target_attack_amplification" in reasons,
        "public_meta_summary_only": True,
        "public_meta_contract_body_allowed": False,
        "public_meta_raw_evidence_allowed": False,
        "public_meta_comment_body_allowed": False,
        "state_answer_contract_body_in_public_meta": False,
        "state_answer_raw_evidence_in_public_meta": False,
        "state_answer_comment_text_body_in_public_meta": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
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
    assert_state_answer_gate_boundary_contract(report)
    return report


def state_answer_gate_boundary_surface_check(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Alias for call sites that name this as an in-memory surface check."""
    return build_state_answer_gate_boundary_report(*args, **kwargs)



def state_answer_gate_boundary_public_summary(value: Any) -> dict[str, Any]:
    source = _as_mapping(value)
    if not source:
        return {}
    if _source_has_unsafe_flags(source):
        return {
            "evaluated": True,
            "passed": False,
            "blocked": True,
            "terminal_surface_block": True,
            "rejection_reasons": ["state_answer_gate_boundary_public_meta_unsafe"],
            "public_meta_summary_only": True,
        }
    summary: dict[str, Any] = {}
    for key in ("evaluated", "passed", "blocked", "terminal_surface_block"):
        if isinstance(source.get(key), bool):
            summary[key] = bool(source.get(key))
    for key in (
        "rejection_reasons",
        "surface_blocker_reasons",
        "forbidden_claim_reasons",
        "allowed_exception_ids",
        "two_stage_reception_gate_rejection_reasons",
        "phase16_7_unavailable_reason_codes",
        "two_stage_unavailable_reason_codes",
    ):
        reasons = _dedupe(source.get(key) or [])
        if reasons:
            summary[key] = reasons[:12]
    for key in (
        "state_answer_surface_contract_connected",
        "self_denial_special_handling_enabled",
        "self_denial_limited_counter_opinion_allowed",
        "self_denial_exception_evidence_ready",
        "anger_special_handling_enabled",
        "anger_target_judgement_agreement_blocked",
        "two_stage_reception_gate_connected",
        "two_stage_reception_gate_terminal_surface_block",
        "two_stage_reception_cross_gate_connected",
        "two_stage_reception_cross_gate_active",
        "two_stage_required_but_unrealized",
        "two_stage_complete_surface_blocked_by_gate",
        "public_meta_summary_only",
    ):
        if isinstance(source.get(key), bool):
            summary[key] = bool(source.get(key))
    nested_two_stage = two_stage_reception_gate_public_summary(source.get("two_stage_reception_gate"))
    if nested_two_stage:
        summary["two_stage_reception_gate"] = nested_two_stage
    if summary:
        summary["public_meta_summary_only"] = True
    assert_state_answer_gate_boundary_contract(summary, source="state_answer_gate_boundary_public_summary")
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


def assert_state_answer_gate_boundary_contract(
    value: Any,
    *,
    source: str = "state_answer_gate_boundary",
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment/evidence payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates public boundary contract: {key}=true")
    schema = _clean(value.get("schema_version"))
    if schema and schema != EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION:
        raise ValueError(f"{source} has unexpected schema_version")
    material_id = _clean(value.get("material_id"))
    if material_id and material_id != EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_MATERIAL_ID:
        raise ValueError(f"{source} has unexpected material_id")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


# Project-local aliases.
build_emlis_ai_state_answer_gate_boundary_report = build_state_answer_gate_boundary_report
assert_emlis_ai_state_answer_gate_boundary_contract = assert_state_answer_gate_boundary_contract

__all__ = [
    "EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_SCHEMA_VERSION",
    "EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_MATERIAL_ID",
    "EMLIS_AI_STATE_ANSWER_GATE_BOUNDARY_PHASE",
    "build_state_answer_gate_boundary_report",
    "state_answer_gate_boundary_surface_check",
    "build_emlis_ai_state_answer_gate_boundary_report",
    "state_answer_gate_boundary_public_summary",
    "assert_state_answer_gate_boundary_contract",
    "assert_emlis_ai_state_answer_gate_boundary_contract",
]
