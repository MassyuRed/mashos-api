# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step1 Runtime Surface Pre-Return Gate contract for EmlisAI.

This module defines the display-pre-return surface quality contract.  It does
not rewrite observation text, does not call external AI, does not change public
API/RN/DB contracts, and does not relax Reader/Grounding/Template/Display gates.

The gate evaluates an in-memory candidate surface and returns meta-only control
information so later steps can decide whether to allow, rerender, reroute, or
fail closed before ``passed + comment_text`` reaches RN.
"""

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from emlis_ai_complete_surface_quality_signature import (
    SURFACE_QUALITY_SIGNATURE_VERSION,
    assert_surface_quality_signature_meta_only,
    build_surface_quality_signature,
    coerce_surface_quality_signature_meta,
)

from emlis_ai_environment_state_output_surface_contract_completion import (
    DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS,
    environment_state_output_scope_marker_present as _shared_environment_state_output_scope_marker_present,
    environment_state_output_surface_rejection_reasons as _shared_environment_state_output_surface_rejection_reasons,
)

from emlis_ai_state_answer_special_cases import (
    state_answer_special_cases_forward_meta,
    state_answer_special_cases_surface_gate_check,
)
from emlis_ai_state_answer_gate_boundary import (
    build_state_answer_gate_boundary_report,
    state_answer_gate_boundary_public_summary,
)

RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION = "emlis.runtime_surface_pre_return_gate.v1"
RUNTIME_SURFACE_PRE_RETURN_GATE_STEP = "Step1_Runtime_Surface_Pre_Return_Gate_Contract"
RUNTIME_SURFACE_PRE_RETURN_GATE_SOURCE = "emlis_runtime_surface_pre_return_gate"

ACTION_ALLOW = "allow"
ACTION_BLOCK = "block"
ACTION_RERENDER_SHALLOW_V2 = "rerender_shallow_v2"
ACTION_REROUTE_LOW_INFORMATION = "reroute_low_information"
ACTION_FAIL_CLOSED = "fail_closed"
RUNTIME_SURFACE_PRE_RETURN_GATE_ACTIONS = (
    ACTION_ALLOW,
    ACTION_BLOCK,
    ACTION_RERENDER_SHALLOW_V2,
    ACTION_REROUTE_LOW_INFORMATION,
    ACTION_FAIL_CLOSED,
)

# These are generic surface-level forms that must not be allowed to cross the
# pre-return boundary.  They intentionally do not match a single screenshot as a
# runtime special case; they describe malformed nominalization patterns.
_MALFORMED_SURFACE_NOMINALIZATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "malformed_nominalization_temporal_fragment",
        re.compile(r"(?:今まで|これまで|さっき|さきほど|まだ|このまま|先ほど)こと"),
    ),
    (
        "malformed_nominalization_adjective_fragment",
        re.compile(r"(?:大丈夫|平気|普通|不安定|曖昧|中途半端|好き|嫌い)こと"),
    ),
    (
        "malformed_nominalization_question_fragment",
        re.compile(r"(?:ないか|なんで|どうして|どれ|どこ|なに|何|しれないどれ)こと"),
    ),
    (
        "malformed_nominalization_te_form_fragment",
        re.compile(r"(?:なくて|ないで|なれなくて|できなくて|ならなくて|なせなくて|しきれなくて)こと"),
    ),
    (
        "malformed_nominalization_tari_fragment",
        re.compile(r"たりこと"),
    ),
    (
        "malformed_nominalization_auxiliary_fragment",
        re.compile(r"(?:しれない|かもしれない|だった|している|見えている)こと(?:も|が|は|に|$)"),
    ),
    (
        "malformed_nominalization_conditional_fragment",
        re.compile(
            r"(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|"
            r"行かなければ|出なければ|やらなければ|取らなければ)こと(?:$|[もがはにをでへ、。,.])"
        ),
    ),
    (
        "malformed_nominalization_prediction_noun_fragment",
        re.compile(r"(?:予感|気配|予定|必要|つもり|はず|可能性|見込み|感じ)こと(?:$|[もがはにをでへ、。,.])"),
    ),
    (
        "residual_koto_splice_fragment",
        re.compile(
            r"(?:ことこと|(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|"
            r"行かなければ|出なければ|やらなければ|取らなければ)こと|予感こと|気配こと|予定こと|"
            r"必要こと|つもりこと|はずこと|可能性こと|見込みこと|感じこと)(?:$|[もがはにをでへ、。,.])"
        ),
    ),
    (
        "long_clause_koto_attachment_risk",
        re.compile(
            r"[^。！？!?\n]{18,120}(?:(?:なければ|なきゃ|ないと|しないと|しなくては|せねば)こと|"
            r"(?:予感|気配|予定|必要|可能性|見込み)こと)(?:$|[もがはにをでへ、。,.])"
        ),
    ),
)

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "input_feedback_comment",
    "inputFeedbackComment",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "line_text",
    "body",
    "text",
    "sentence",
    "sentences",
    "phrase",
    "raw_quote",
    "raw_quotes",
    "matched_raw_quote_fragments",
}

_CONTRACT_TRUE_FLAGS = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "public_release_applied",
    "product_gate_achieved",
    "fixed_sentence_template_added",
    "input_specific_template_used",
    "external_ai_used",
    "local_llm_used",
)

_REQUIRED_REPORT_KEYS = (
    "version",
    "evaluated",
    "passed",
    "action",
    "rejection_reasons",
    "raw_input_included",
    "comment_text_body_included",
    "display_gate_relaxed",
)

_SHALLOW_PROFILE_KEYS = {
    "current_input_core",
    "shallow",
    "limited_current_input_core",
    "limited_shallow",
}

_ENV_STATE_OUTPUT_SCOPE_MARKERS = DEFAULT_ENVIRONMENT_STATE_OUTPUT_SCOPE_MARKERS
_ENV_STATE_OUTPUT_PERIOD_TENDENCY_RE = re.compile(
    r"(?:いつも|毎回|たびに|度に|よく|繰り返し|くり返し|傾向|出やすい|なりやすい|しやすい|パターン)"
)
_ENV_STATE_OUTPUT_PERSONALITY_RE = re.compile(r"(?:タイプ|性格|人格|本質|こういう人|診断|症状|病気|トラウマ|障害)")
_ENV_STATE_OUTPUT_CAUSE_RE = re.compile(r"(?:原因は|原因です|原因として|原因にな|カテゴリ.*原因|仕事.*原因|人間関係.*原因|感情.*原因)")
_ENV_STATE_OUTPUT_RECOVERY_RE = re.compile(
    r"(?:回復方法|治る|治ります|解決策|こうすれば|すれば戻れ|戻りやすい|戻れます|必要があります|すべきです|するべきです)"
)

_ENV_STATE_OUTPUT_TERMINAL_SURFACE_REASONS = {
    "environment_state_output_scope_marker_missing",
    "period_tendency_from_single_record_surface",
    "personality_tendency_surface",
    "diagnosis_surface",
    "cause_from_category_surface",
    "cause_from_emotion_strength_surface",
    "recovery_prescription_surface",
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, Mapping) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        source: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        source = values
    else:
        source = [values]
    out: list[str] = []
    seen: set[str] = set()
    for raw in source:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_pre_return_gate_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = RUNTIME_SURFACE_PRE_RETURN_GATE_SOURCE,
) -> None:
    """Validate that a pre-return gate report is contract/meta-only."""

    data = _safe_mapping(value)
    missing = [key for key in _REQUIRED_REPORT_KEYS if key not in data]
    if missing:
        raise ValueError(f"{source} is missing required keys: {missing}")
    if _contains_forbidden_text_payload_key(data):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    action = _clean(data.get("action"))
    if action not in RUNTIME_SURFACE_PRE_RETURN_GATE_ACTIONS:
        raise ValueError(f"{source} has invalid action: {action}")
    if not isinstance(data.get("rejection_reasons"), list):
        raise ValueError(f"{source} rejection_reasons must be a list")
    if not isinstance(data.get("passed"), bool) or not isinstance(data.get("evaluated"), bool):
        raise ValueError(f"{source} passed/evaluated must be boolean")
    for flag in _CONTRACT_TRUE_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def build_runtime_surface_pre_return_gate_contract_schema() -> dict[str, Any]:
    """Return the Step1 pre-return gate report schema contract.

    The schema is an in-code contract object, not a persisted JSON artifact.
    """

    return {
        "$id": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "type": "object",
        "required": list(_REQUIRED_REPORT_KEYS),
        "properties": {
            "version": {"const": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION},
            "evaluated": {"type": "boolean"},
            "passed": {"type": "boolean"},
            "blocked": {"type": "boolean"},
            "action": {"type": "string", "enum": list(RUNTIME_SURFACE_PRE_RETURN_GATE_ACTIONS)},
            "rejection_reasons": {"type": "array", "items": {"type": "string"}},
            "surface_signature_id": {"type": "string"},
            "surface_template_major": {"type": "boolean"},
            "generic_center_phrase_count": {"type": "integer", "minimum": 0},
            "same_connector_run_max": {"type": "integer", "minimum": 0},
            "same_connector_repetition_count": {"type": "integer", "minimum": 0},
            "grammar_warning_count": {"type": "integer", "minimum": 0},
            "malformed_phrase_unit_count": {"type": "integer", "minimum": 0},
            "surface_malformed_nominalization_codes": {"type": "array", "items": {"type": "string"}},
            "koto_splice_detected": {"type": "boolean"},
            "koto_splice_codes": {"type": "array", "items": {"type": "string"}},
            "rerender_allowed": {"type": "boolean"},
            "rerender_attempted": {"type": "boolean"},
            "rerender_attempt_limit": {"type": "integer", "minimum": 0, "maximum": 1},
            "raw_input_included": {"const": False},
            "comment_text_body_included": {"const": False},
            "display_gate_relaxed": {"const": False},
        },
    }


def _surface_signature_from_inputs(
    *,
    comment_text: Any,
    surface_quality_signature: Mapping[str, Any] | None,
    phrase_unit_grammar_meta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    provided = coerce_surface_quality_signature_meta(surface_quality_signature)
    if provided.get("surface_signature_id"):
        assert_surface_quality_signature_meta_only(provided, source="runtime_pre_return_surface_signature")
        return provided
    text = _clean(comment_text)
    if not text:
        return {}
    return build_surface_quality_signature(
        comment_text=text,
        phrase_unit_grammar_meta=phrase_unit_grammar_meta,
    )


def _surface_malformed_nominalization_codes(comment_text: Any) -> list[str]:
    text = _clean(comment_text)
    if not text:
        return []
    codes: list[str] = []
    for code, pattern in _MALFORMED_SURFACE_NOMINALIZATION_PATTERNS:
        if pattern.search(text):
            codes.append(code)
    return _dedupe(codes)


def _is_malformed_nominalization_code(code: Any) -> bool:
    value = _clean(code)
    return bool(
        value.startswith("malformed_nominalization_")
        or value.startswith("stem_koto_")
        or value in {"residual_koto_splice_fragment", "long_clause_koto_attachment_risk"}
    )


def _surface_signature_malformed_nominalization_codes(signature: Mapping[str, Any]) -> list[str]:
    if not signature:
        return []
    sources: list[Any] = []
    for key in (
        "surface_malformed_nominalization_codes",
        "malformed_nominalization_codes",
        "surface_grammar_warning_codes",
        "grammar_warning_codes",
        "phrase_unit_grammar_warning_codes",
        "line_grammar_warning_codes",
    ):
        value = signature.get(key)
        if isinstance(value, (list, tuple, set)):
            sources.extend(value)
    return _dedupe(code for code in sources if _is_malformed_nominalization_code(code))


def _malformed_phrase_unit_count(
    *,
    signature: Mapping[str, Any],
    surface_malformed_codes: Sequence[str],
    phrase_unit_grammar_meta: Mapping[str, Any] | None,
) -> int:
    meta = _safe_mapping(phrase_unit_grammar_meta)
    explicit_raw = (
        meta.get("malformed_phrase_unit_count")
        if "malformed_phrase_unit_count" in meta
        else meta.get("malformed_nominalization_count")
        if "malformed_nominalization_count" in meta
        else meta.get("phrase_unit_malformed_count")
        if "phrase_unit_malformed_count" in meta
        else None
    )
    surface_malformed_count = len(_dedupe(surface_malformed_codes or []))
    if explicit_raw is not None:
        return max(0, _safe_int(explicit_raw), surface_malformed_count)
    warning_codes = _dedupe(
        list(signature.get("phrase_unit_grammar_warning_codes") or [])
        + list(signature.get("surface_grammar_warning_codes") or [])
        + list(signature.get("grammar_warning_codes") or [])
        + list(signature.get("surface_malformed_nominalization_codes") or [])
        + list(signature.get("malformed_nominalization_codes") or [])
        + list(surface_malformed_codes or [])
    )
    warning_count = len([code for code in warning_codes if _is_malformed_nominalization_code(code)])
    explicit_signature_count = _safe_int(
        signature.get("surface_malformed_phrase_unit_count")
        or signature.get("malformed_phrase_unit_count")
    )
    return max(warning_count, surface_malformed_count, explicit_signature_count)


def _is_shallow_observation_path(composer_meta: Mapping[str, Any] | None) -> bool:
    meta = _safe_mapping(composer_meta)
    profile_key = _clean(meta.get("profile_key") or meta.get("composer_profile_key"))
    coverage_scope = _clean(meta.get("coverage_scope"))
    return bool(
        meta.get("shallow_observation_path") is True
        or meta.get("current_input_core_path") is True
        or profile_key in _SHALLOW_PROFILE_KEYS
        or coverage_scope in _SHALLOW_PROFILE_KEYS
    )


def _state_answer_special_cases_from_inputs(
    *,
    state_answer_special_cases: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    explicit = state_answer_special_cases_forward_meta(state_answer_special_cases)
    if explicit:
        return explicit
    meta = _safe_mapping(composer_meta)
    for key in ("state_answer_special_cases", "state_answer_special_cases_payload", "special_handling"):
        found = state_answer_special_cases_forward_meta(meta.get(key))
        if found:
            return found
    contract = _safe_mapping(meta.get("state_answer_surface_contract"))
    for key in ("special_handling", "state_answer_special_cases", "state_answer_special_cases_payload"):
        found = state_answer_special_cases_forward_meta(contract.get(key))
        if found:
            return found
    return {}


def _environment_state_output_surface_contract(composer_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(composer_meta)
    contract = meta.get("environment_state_output_surface_contract")
    if isinstance(contract, Mapping):
        return dict(contract)
    structure = meta.get("observation_structure_material") or meta.get("observation_structure_dictionary")
    if isinstance(structure, Mapping):
        frame = structure.get("environment_state_output_frame")
        if isinstance(frame, Mapping) and frame:
            frame_policy = frame.get("frame_policy") if isinstance(frame.get("frame_policy"), Mapping) else {}
            output_axis = frame.get("output_axis") if isinstance(frame.get("output_axis"), Mapping) else {}
            return {
                "connected": True,
                "single_record_only": True,
                "scope_marker_required": True,
                "allowed_scope_markers": list(_ENV_STATE_OUTPUT_SCOPE_MARKERS),
                "required_scope_marker": _clean(frame_policy.get("scope_marker")) or "今回の入力では",
                "allowed_surface_claim_strength": "single_observation",
                "output_theme_ids": list(output_axis.get("output_theme_ids") or []),
            }
    if bool(meta.get("environment_state_output_frame_limited_use")):
        return {
            "connected": True,
            "single_record_only": True,
            "scope_marker_required": bool(meta.get("environment_state_output_scope_marker_required", True)),
            "allowed_scope_markers": list(meta.get("environment_state_output_allowed_scope_markers") or _ENV_STATE_OUTPUT_SCOPE_MARKERS),
            "required_scope_marker": "今回の入力では",
            "allowed_surface_claim_strength": _clean(meta.get("environment_state_output_allowed_surface_claim_strength")) or "single_observation",
            "output_theme_ids": list(meta.get("environment_state_output_output_theme_ids") or []),
        }
    return {}


def _environment_state_output_surface_rejection_reasons(
    *,
    comment_text: Any,
    composer_meta: Mapping[str, Any] | None,
) -> list[str]:
    contract = _environment_state_output_surface_contract(composer_meta)
    if not bool(contract.get("connected")):
        return []
    text = _clean(comment_text)
    if not text:
        if bool(contract.get("scope_marker_required", False)):
            return ["environment_state_output_scope_marker_missing"]
        return []
    return _dedupe(_shared_environment_state_output_surface_rejection_reasons(text, contract))


def _environment_state_output_terminal_surface_block(reasons: Sequence[str]) -> bool:
    return any(_clean(reason) in _ENV_STATE_OUTPUT_TERMINAL_SURFACE_REASONS for reason in reasons)


def _surface_rejection_reasons(
    *,
    signature: Mapping[str, Any],
    surface_malformed_codes: Sequence[str],
    signature_malformed_codes: Sequence[str],
    malformed_phrase_unit_count: int,
) -> list[str]:
    if not signature:
        return ["surface_signature_unavailable"]
    reasons: list[str] = []
    line_count = _safe_int(signature.get("line_count"))
    body_sentence_count = _safe_int(signature.get("body_sentence_count"))
    body_line_count = max(0, line_count - 1) if line_count else body_sentence_count
    generic_center_phrase_count = _safe_int(signature.get("generic_center_phrase_count"))
    same_connector_run_max = _safe_int(signature.get("same_connector_run_max"))
    same_connector_repetition_count = _safe_int(signature.get("same_connector_repetition_count"))
    grammar_warning_count = _safe_int(
        signature.get("surface_grammar_warning_count")
        or signature.get("grammar_warning_count")
        or len(signature.get("grammar_warning_codes") or [])
    )
    if bool(signature.get("surface_template_major") or signature.get("template_major")):
        reasons.append("surface_template_major")
    if generic_center_phrase_count > 0:
        reasons.append("generic_center_phrase")
    if same_connector_run_max >= 2:
        reasons.append("same_connector_run")
    if generic_center_phrase_count > 0 and same_connector_run_max >= 2:
        reasons.extend(["surface_template_skeleton", "connector_repetition"])
    if same_connector_repetition_count >= 1 and (body_line_count <= 4 or body_sentence_count <= 4):
        reasons.extend(["same_connector_repetition", "surface_connector_repetition"])
    if grammar_warning_count > 0:
        reasons.append("surface_grammar_warning")
    if bool(signature.get("malformed_nominalization_risk")):
        reasons.append("malformed_nominalization_risk")
    if malformed_phrase_unit_count > 0:
        reasons.append("malformed_phrase_unit")
    malformed_codes = _dedupe([*surface_malformed_codes, *signature_malformed_codes])
    reasons.extend(malformed_codes)
    if any(_is_malformed_nominalization_code(reason) for reason in malformed_codes):
        reasons.append("malformed_nominalization_risk")
    return _dedupe(reasons)


def _action_for_reasons(
    *,
    reasons: Sequence[str],
    shallow_observation_path: bool,
    rerender_allowed: bool,
    rerender_attempted: bool,
    low_information_reroute_allowed: bool,
    terminal_surface_block: bool = False,
) -> str:
    if not reasons:
        return ACTION_ALLOW
    if "surface_signature_unavailable" in reasons:
        return ACTION_FAIL_CLOSED
    if terminal_surface_block:
        return ACTION_BLOCK
    if shallow_observation_path and rerender_allowed and not rerender_attempted:
        return ACTION_RERENDER_SHALLOW_V2
    if low_information_reroute_allowed and not rerender_attempted:
        return ACTION_REROUTE_LOW_INFORMATION
    return ACTION_BLOCK


def build_runtime_surface_pre_return_gate_report(
    *,
    comment_text: Any = "",
    composer_meta: Mapping[str, Any] | None = None,
    surface_quality_signature: Mapping[str, Any] | None = None,
    phrase_unit_grammar_meta: Mapping[str, Any] | None = None,
    rerender_allowed: bool = True,
    rerender_attempted: bool = False,
    rerender_attempt_limit: int = 1,
    low_information_reroute_allowed: bool = False,
    state_answer_special_cases: Any = None,
    state_answer_surface_contract: Any = None,
) -> dict[str, Any]:
    """Build a meta-only Step1 pre-return gate report.

    ``comment_text`` is accepted only as in-memory evaluation material.  The
    returned report intentionally contains no raw input and no candidate body.
    """

    signature = _surface_signature_from_inputs(
        comment_text=comment_text,
        surface_quality_signature=surface_quality_signature,
        phrase_unit_grammar_meta=phrase_unit_grammar_meta,
    )
    surface_malformed_codes = _surface_malformed_nominalization_codes(comment_text)
    signature_malformed_codes = _surface_signature_malformed_nominalization_codes(signature)
    malformed_count = _malformed_phrase_unit_count(
        signature=signature,
        surface_malformed_codes=_dedupe([*surface_malformed_codes, *signature_malformed_codes]),
        phrase_unit_grammar_meta=phrase_unit_grammar_meta,
    )
    surface_malformed_codes = _dedupe([*surface_malformed_codes, *signature_malformed_codes])
    reasons = _surface_rejection_reasons(
        signature=signature,
        surface_malformed_codes=surface_malformed_codes,
        signature_malformed_codes=signature_malformed_codes,
        malformed_phrase_unit_count=malformed_count,
    )
    environment_state_output_contract = _environment_state_output_surface_contract(composer_meta)
    environment_state_output_reasons = _environment_state_output_surface_rejection_reasons(
        comment_text=comment_text,
        composer_meta=composer_meta,
    )
    special_cases_meta = _state_answer_special_cases_from_inputs(
        state_answer_special_cases=state_answer_special_cases,
        composer_meta=composer_meta,
    )
    special_case_surface_report = state_answer_special_cases_surface_gate_check(
        visible_surface=comment_text,
        special_cases=special_cases_meta,
    )
    state_answer_gate_boundary_report = build_state_answer_gate_boundary_report(
        visible_surface=comment_text,
        state_answer_surface_contract=state_answer_surface_contract,
        state_answer_special_cases=special_cases_meta,
        composer_meta=composer_meta,
    )
    special_case_reasons = _dedupe(special_case_surface_report.get("surface_blocker_reasons") or [])
    state_answer_gate_boundary_reasons = _dedupe(
        state_answer_gate_boundary_report.get("surface_blocker_reasons")
        or state_answer_gate_boundary_report.get("rejection_reasons")
        or []
    )
    environment_state_output_terminal_block = _environment_state_output_terminal_surface_block(environment_state_output_reasons)
    special_case_terminal_block = bool(special_case_reasons)
    state_answer_gate_boundary_terminal_block = bool(
        state_answer_gate_boundary_report.get("terminal_surface_block") or state_answer_gate_boundary_reasons
    )
    environment_state_output_marker_present = bool(
        environment_state_output_contract.get("connected")
        and _shared_environment_state_output_scope_marker_present(comment_text, environment_state_output_contract)
    )
    reasons = _dedupe([*reasons, *environment_state_output_reasons, *special_case_reasons, *state_answer_gate_boundary_reasons])
    shallow_path = _is_shallow_observation_path(composer_meta)
    action = _action_for_reasons(
        reasons=reasons,
        shallow_observation_path=shallow_path,
        rerender_allowed=bool(rerender_allowed),
        rerender_attempted=bool(rerender_attempted),
        low_information_reroute_allowed=bool(low_information_reroute_allowed),
        terminal_surface_block=(
            environment_state_output_terminal_block
            or special_case_terminal_block
            or state_answer_gate_boundary_terminal_block
        ),
    )
    passed = action == ACTION_ALLOW and not reasons
    report: dict[str, Any] = {
        "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "schema_version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "source": RUNTIME_SURFACE_PRE_RETURN_GATE_SOURCE,
        "source_step": RUNTIME_SURFACE_PRE_RETURN_GATE_STEP,
        "step": RUNTIME_SURFACE_PRE_RETURN_GATE_STEP,
        "runtime_surface_pre_return_gate_ready": True,
        "runtime_surface_pre_return_gate_contract_ready": True,
        "evaluated": True,
        "passed": passed,
        "blocked": not passed,
        "action": action,
        "rerender_recommended": action == ACTION_RERENDER_SHALLOW_V2,
        "reroute_low_information_recommended": action == ACTION_REROUTE_LOW_INFORMATION,
        "rejection_reasons": list(reasons),
        "surface_signature_ready": bool(signature.get("surface_signature_id")),
        "surface_signature_version": signature.get("schema_version") or SURFACE_QUALITY_SIGNATURE_VERSION,
        "surface_signature_id": _clean(signature.get("surface_signature_id")),
        "surface_template_major": bool(signature.get("surface_template_major") or signature.get("template_major")),
        "generic_center_phrase_count": _safe_int(signature.get("generic_center_phrase_count")),
        "same_connector_run_max": _safe_int(signature.get("same_connector_run_max")),
        "same_connector_repetition_count": _safe_int(signature.get("same_connector_repetition_count")),
        "grammar_warning_count": _safe_int(
            signature.get("surface_grammar_warning_count")
            or signature.get("grammar_warning_count")
            or len(signature.get("grammar_warning_codes") or [])
        ),
        "malformed_nominalization_risk": bool(signature.get("malformed_nominalization_risk") or surface_malformed_codes),
        "malformed_phrase_unit_count": int(malformed_count),
        "surface_malformed_nominalization_codes": list(surface_malformed_codes),
        "koto_splice_detected": any(
            code in {
                "malformed_nominalization_conditional_fragment",
                "malformed_nominalization_prediction_noun_fragment",
                "residual_koto_splice_fragment",
                "long_clause_koto_attachment_risk",
            }
            for code in surface_malformed_codes
        ),
        "koto_splice_codes": [
            code
            for code in surface_malformed_codes
            if code in {
                "malformed_nominalization_conditional_fragment",
                "malformed_nominalization_prediction_noun_fragment",
                "residual_koto_splice_fragment",
                "long_clause_koto_attachment_risk",
            }
        ],
        "shallow_observation_path": bool(shallow_path),
        "rerender_allowed": bool(rerender_allowed),
        "rerender_attempted": bool(rerender_attempted),
        "rerender_attempt_limit": max(0, min(1, _safe_int(rerender_attempt_limit, default=1))),
        "low_information_reroute_allowed": bool(low_information_reroute_allowed),
        "environment_state_output_frame_surface_limited_use": bool(environment_state_output_contract.get("connected")),
        "environment_state_output_single_record_only": bool(environment_state_output_contract.get("single_record_only", False)),
        "environment_state_output_scope_marker_required": bool(environment_state_output_contract.get("scope_marker_required", False)),
        "environment_state_output_scope_marker_present": bool(environment_state_output_marker_present),
        "environment_state_output_runtime_marker_check_performed": bool(
            environment_state_output_contract.get("connected")
            and environment_state_output_contract.get("scope_marker_required", False)
        ),
        "environment_state_output_runtime_double_check_active": bool(environment_state_output_contract.get("connected")),
        "environment_state_output_runtime_gate_repair_applied": False,
        "environment_state_output_terminal_surface_block": bool(environment_state_output_terminal_block),
        "environment_state_output_allowed_surface_claim_strength": _clean(
            environment_state_output_contract.get("allowed_surface_claim_strength")
        ),
        "environment_state_output_output_theme_ids": list(environment_state_output_contract.get("output_theme_ids") or []),
        "environment_state_output_surface_rejection_reasons": list(environment_state_output_reasons),
        "state_answer_special_case_surface_guard": _safe_mapping(special_case_surface_report),
        "state_answer_special_case_surface_rejection_reasons": list(special_case_reasons),
        "state_answer_special_case_terminal_surface_block": bool(special_case_terminal_block),
        "state_answer_special_case_allowed_exception_ids": list(special_case_surface_report.get("allowed_exception_ids_detected") or []),
        "self_denial_limited_counter_opinion_allowed_by_special_case": bool(
            special_case_surface_report.get("self_denial_limited_counter_opinion_allowed")
        ),
        "anger_target_judgement_agreement_blocked_by_special_case": bool(
            special_case_surface_report.get("anger_target_judgement_agreement_detected")
        ),
        "state_answer_gate_boundary": state_answer_gate_boundary_public_summary(state_answer_gate_boundary_report),
        "state_answer_gate_boundary_rejection_reasons": list(state_answer_gate_boundary_reasons),
        "state_answer_gate_boundary_terminal_surface_block": bool(state_answer_gate_boundary_terminal_block),
        "state_answer_forbidden_claim_reasons": list(state_answer_gate_boundary_report.get("forbidden_claim_reasons") or []),
        "state_answer_allowed_exception_ids": list(
            state_answer_gate_boundary_report.get("allowed_exception_ids_detected")
            or state_answer_gate_boundary_report.get("allowed_exception_ids")
            or []
        ),
        "state_answer_public_meta_summary_only": True,
        "state_answer_contract_body_returned": False,
        "state_answer_raw_evidence_included": False,
        "self_denial_limited_counter_opinion_allowed_by_state_answer_boundary": bool(
            state_answer_gate_boundary_report.get("self_denial_limited_counter_opinion_allowed")
        ),
        "anger_target_judgement_agreement_blocked_by_state_answer_boundary": bool(
            state_answer_gate_boundary_report.get("anger_target_judgement_agreement_blocked")
        ),
        "period_tendency_from_single_record_surface_blocked": "period_tendency_from_single_record_surface" in environment_state_output_reasons,
        "personality_tendency_surface_blocked": "personality_tendency_surface" in environment_state_output_reasons,
        "cause_from_category_surface_blocked": "cause_from_category_surface" in environment_state_output_reasons,
        "cause_from_emotion_strength_surface_blocked": "cause_from_emotion_strength_surface" in environment_state_output_reasons,
        "diagnosis_surface_blocked": "diagnosis_surface" in environment_state_output_reasons,
        "recovery_prescription_surface_blocked": "recovery_prescription_surface" in environment_state_output_reasons,
        "period_tendency_from_single_record": False,
        "recovery_prescription_allowed": False,
        "personality_tendency_allowed": False,
        "diagnosis_allowed": False,
        "cause_inferred_from_category": False,
        "cause_inferred_from_emotion_strength": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    assert_runtime_surface_pre_return_gate_meta_only(report)
    return report


def evaluate_runtime_surface_pre_return_gate(**kwargs: Any) -> dict[str, Any]:
    """Alias kept for call sites that use evaluator naming."""
    return build_runtime_surface_pre_return_gate_report(**kwargs)


def build_runtime_surface_pre_return_gate_contract_meta() -> dict[str, Any]:
    report = {
        "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "schema_version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "source": RUNTIME_SURFACE_PRE_RETURN_GATE_SOURCE,
        "source_step": RUNTIME_SURFACE_PRE_RETURN_GATE_STEP,
        "step": RUNTIME_SURFACE_PRE_RETURN_GATE_STEP,
        "runtime_surface_pre_return_gate_ready": True,
        "runtime_surface_pre_return_gate_contract_ready": True,
        "evaluated": True,
        "passed": True,
        "blocked": False,
        "action": ACTION_ALLOW,
        "rejection_reasons": [],
        "surface_signature_ready": False,
        "surface_signature_version": SURFACE_QUALITY_SIGNATURE_VERSION,
        "surface_signature_id": "",
        "surface_template_major": False,
        "generic_center_phrase_count": 0,
        "same_connector_run_max": 0,
        "same_connector_repetition_count": 0,
        "grammar_warning_count": 0,
        "malformed_nominalization_risk": False,
        "malformed_phrase_unit_count": 0,
        "surface_malformed_nominalization_codes": [],
        "koto_splice_detected": False,
        "koto_splice_codes": [],
        "rerender_allowed": False,
        "rerender_attempted": False,
        "rerender_attempt_limit": 1,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    assert_runtime_surface_pre_return_gate_meta_only(report)
    return report


def dump_runtime_surface_pre_return_gate_report(report: Mapping[str, Any]) -> str:
    data = dict(report or {})
    data.setdefault("raw_input_included", False)
    data.setdefault("raw_text_included", False)
    data.setdefault("input_text_included", False)
    data.setdefault("comment_text_included", False)
    data.setdefault("comment_text_body_included", False)
    assert_runtime_surface_pre_return_gate_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "ACTION_ALLOW",
    "ACTION_BLOCK",
    "ACTION_FAIL_CLOSED",
    "ACTION_RERENDER_SHALLOW_V2",
    "ACTION_REROUTE_LOW_INFORMATION",
    "RUNTIME_SURFACE_PRE_RETURN_GATE_ACTIONS",
    "RUNTIME_SURFACE_PRE_RETURN_GATE_SOURCE",
    "RUNTIME_SURFACE_PRE_RETURN_GATE_STEP",
    "RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION",
    "assert_runtime_surface_pre_return_gate_meta_only",
    "build_runtime_surface_pre_return_gate_contract_meta",
    "build_runtime_surface_pre_return_gate_contract_schema",
    "build_runtime_surface_pre_return_gate_report",
    "dump_runtime_surface_pre_return_gate_report",
    "evaluate_runtime_surface_pre_return_gate",
]
