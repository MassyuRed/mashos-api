# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 9 Structure Insight Gate for EmlisAI.

The gate decides whether Phase 7 Structure Insight candidates may proceed to a
later surface connection.  It is deliberately meta-only: it inspects a proposed
surface string only in memory, never returns the surface body, never writes
``comment_text``, never adds public response keys, and never relaxes the
existing Reader/Grounding/Template/Display boundaries.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
import re
from typing import Any, Final

from emlis_ai_input_material_bundle import MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
from emlis_ai_structure_insight_candidate import (
    EmlisStructureInsightCandidateMaterial,
    RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    RELATION_VALUE_LINE_CROSSED,
    STRUCTURE_INSIGHT_CANDIDATE_VERSION,
    assert_structure_insight_candidate_meta_only,
    build_structure_insight_candidate_meta,
)

STRUCTURE_INSIGHT_GATE_VERSION: Final = "cocolon.emlis.structure_insight_gate.v1"
STRUCTURE_INSIGHT_GATE_FIELDS_VERSION: Final = "cocolon.emlis.structure_insight_gate.scorecard_fields.v1"
STRUCTURE_INSIGHT_GATE_PHASE9_STEP: Final = "Phase9_Structure_Insight_Gate"
STRUCTURE_INSIGHT_GATE_STEP: Final = STRUCTURE_INSIGHT_GATE_PHASE9_STEP
STRUCTURE_INSIGHT_GATE_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase9_StructureInsightGate"

GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE: Final = "allow_internal_surface_candidate"
GATE_ACTION_BLOCK_SURFACE_CANDIDATE: Final = "block_surface_candidate"
GATE_ACTION_NO_CANDIDATE: Final = "no_candidate"

_SPACE_RE: Final = re.compile(r"\s+")
_SOFT_MARKER_RE: Final = re.compile(
    r"(?:ように見えます|ようにも見えます|かもしれません|ではないでしょうか|ではないかと思います|近い状態かもしれません|重なっているように見えます|残っているのかもしれません|として残っているのかもしれません)"
)
_DIAGNOSIS_RE: Final = re.compile(
    r"(?:診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|PTSD|医学的|心理学的)"
)
_PERSONALITY_CLAIM_RE: Final = re.compile(
    r"(?:あなたは(?:[^。！？!?\n]{0,24})(?:人です|タイプです|性格です|本質です|依存しています|弱い人|強い人|ダメな人|駄目な人)|(?:性格|人格|本質|タイプ)(?:です|だから))"
)
_CAUSE_CLAIM_RE: Final = re.compile(
    r"(?:原因は|原因です|原因になっています|本当の原因|理由はひとつ|カテゴリが原因|感情の強さが原因|だからあなたは|だから本当は)"
)
_ADVICE_RE: Final = re.compile(
    r"(?:してください|しましょう|するべき|すべき|しなければ|しなくてはいけません|必要があります|距離を取(?:った|る)方がいい|連絡しましょう|相談しましょう|決めましょう)"
)
_PERIOD_TENDENCY_RE: Final = re.compile(
    r"(?:いつも|毎回|ずっと|長い間|たびに|度に|繰り返し|くり返し|傾向|パターン|なりやすい|しやすい|出やすい)"
)
_TARGET_JUDGEMENT_RE: Final = re.compile(
    r"(?:(?:相手|上司|あの人|その人|彼|彼女|会社|職場)[^。！？!?\n]{0,28}(?:悪い|ひどい|最低|おかしい|間違って|軽く見て|見下して|敵)|あなたの怒りは(?:正しい|当然)|相手が悪い|上司が悪い|攻撃していい)"
)
_TARGET_INTENT_RE: Final = re.compile(
    r"(?:(?:相手|上司|あの人|その人|彼|彼女|会社|職場)[^。！？!?\n]{0,28}(?:思っています|思っている|考えています|考えている|わざと|意図して|見下しています|軽く見ています))"
)
_SELF_DENIAL_IDENTITY_FACT_RE: Final = re.compile(
    r"(?:あなたは(?:[^。！？!?\n]{0,16})(?:ダメ|駄目|価値がない|何もできない|弱い|嫌な人)|自分が嫌なのは事実|何もできない状態です|価値がない状態です)"
)
_LOW_INFORMATION_OVERREAD_RE: Final = re.compile(
    r"(?:本当は|深いところでは|根本には|背景には|原因は|ずっと我慢してきた)"
)

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
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
        "current_input",
        "currentInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "emotion_details",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "realized_text",
        "display_text",
        "observation_text",
        "reception_text",
        "candidate_body",
        "surface_body",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "candidate_surface_generated",
    "candidate_body_generated",
    "comment_text_generated",
    "comment_text_key_written",
    "comment_text_written_by_gate",
    "comment_text_written_by_candidate",
    "comment_text_written_by_scorecard",
    "public_response_key_added",
    "public_response_key_change",
    "public_payload_changed",
    "response_shape_changed",
    "api_route_changed",
    "request_key_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "product_gate_ready",
    "product_gate_reached",
    "public_release_applied",
    "product_quality_released",
    "external_ai_used",
    "local_llm_used",
    "diagnosis_allowed",
    "personality_claim_allowed",
    "cause_claim_allowed",
    "advice_allowed",
    "target_judgement_agreement_allowed",
    "period_tendency_from_single_record_allowed",
    "user_dictionary_fact_claim_allowed",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return _SPACE_RE.sub(" ", str(value).replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


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
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _flag_true(value: Any, names: Iterable[str]) -> bool:
    wanted = {str(name) for name in names}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in wanted and item is True:
                return True
            if _flag_true(item, wanted):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_flag_true(item, wanted) for item in value)
    return False


def _coerce_candidate_material_meta(
    material: EmlisStructureInsightCandidateMaterial | Mapping[str, Any] | None,
    *,
    current_input: Any = None,
    run_id: str = "",
) -> dict[str, Any]:
    if isinstance(material, EmlisStructureInsightCandidateMaterial):
        data = material.as_meta()
    elif isinstance(material, Mapping) and material:
        data = dict(material)
    else:
        data = build_structure_insight_candidate_meta(current_input or {}, run_id=run_id)
    assert_structure_insight_candidate_meta_only(data)
    return data


def _surface_rejection_reasons(
    *,
    surface: str,
    relation_family: str,
    material_quality: str,
    strict_context_reasons: Sequence[str],
) -> list[str]:
    if not surface:
        return []
    reasons: list[str] = []
    if not _SOFT_MARKER_RE.search(surface):
        reasons.append("soft_expression_missing")
    if _DIAGNOSIS_RE.search(surface):
        reasons.append("diagnosis_surface")
    if _PERSONALITY_CLAIM_RE.search(surface):
        reasons.append("personality_claim_surface")
    if _CAUSE_CLAIM_RE.search(surface):
        reasons.append("cause_claim_without_evidence_surface")
    if _ADVICE_RE.search(surface):
        reasons.append("advice_surface")
    if _PERIOD_TENDENCY_RE.search(surface):
        reasons.append("period_tendency_from_single_record_surface")
    if _TARGET_JUDGEMENT_RE.search(surface):
        reasons.append("target_judgement_agreement_surface")
    if _TARGET_INTENT_RE.search(surface):
        reasons.append("opponent_intent_claim_surface")
    if relation_family == RELATION_SELF_DENIAL_IDENTITY_SPLIT and _SELF_DENIAL_IDENTITY_FACT_RE.search(surface):
        reasons.append("self_denial_identity_claim_as_fact_surface")
    if relation_family == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT and _LOW_INFORMATION_OVERREAD_RE.search(surface):
        reasons.append("low_information_background_overread_surface")
    if material_quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED:
        reasons.append("safety_adjacent_insight_surface_blocked")
    if "anger_or_boundary_strict_context" in strict_context_reasons and (
        _TARGET_JUDGEMENT_RE.search(surface) or _TARGET_INTENT_RE.search(surface)
    ):
        reasons.append("anger_or_boundary_strict_gate_blocked")
    if "self_denial_strict_context" in strict_context_reasons and _SELF_DENIAL_IDENTITY_FACT_RE.search(surface):
        reasons.append("self_denial_strict_gate_blocked")
    return _dedupe(reasons)


def _candidate_evidence(candidate: Mapping[str, Any]) -> dict[str, Any]:
    evidence = _safe_mapping(candidate.get("evidence"))
    return {
        "source_field_ids": _dedupe(evidence.get("source_field_ids") or candidate.get("source_field_ids") or []),
        "evidence_slot_count": _int(evidence.get("evidence_slot_count") or candidate.get("evidence_slot_count")),
        "requires_external_knowledge": bool(evidence.get("requires_external_knowledge")),
        "requires_user_history": bool(evidence.get("requires_user_history")),
    }


def _strict_context_reasons(
    *,
    relation_family: str,
    forbidden_claims: Sequence[str],
    material_quality: str,
) -> list[str]:
    claims = set(_dedupe(forbidden_claims))
    reasons: list[str] = []
    if relation_family == RELATION_VALUE_LINE_CROSSED or {"target_judgement_agreement", "target_attack_agreement", "opponent_intent_claim"}.intersection(claims):
        reasons.append("anger_or_boundary_strict_context")
    if relation_family == RELATION_SELF_DENIAL_IDENTITY_SPLIT or {"identity_claim_as_fact", "self_denial_accepted_as_user_fact"}.intersection(claims):
        reasons.append("self_denial_strict_context")
    if material_quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED:
        reasons.append("safety_adjacent_strict_context")
    return _dedupe(reasons)


def _candidate_gate_result(
    *,
    candidate: Mapping[str, Any],
    material_quality: str,
    proposed_surface: str,
    surface_candidate_meta: Mapping[str, Any],
    user_dictionary_meta: Mapping[str, Any],
) -> dict[str, Any]:
    relation_family = _clean(candidate.get("relation_family"))
    candidate_id = _clean(candidate.get("candidate_id")) or relation_family or "candidate"
    candidate_quality = _clean(candidate.get("candidate_quality")) or "unknown"
    evidence = _candidate_evidence(candidate)
    surface_permission = _safe_mapping(candidate.get("surface_permission"))
    forbidden_claims = _dedupe(candidate.get("forbidden_claims") or [])
    strict_context = _strict_context_reasons(
        relation_family=relation_family,
        forbidden_claims=forbidden_claims,
        material_quality=material_quality,
    )

    reasons: list[str] = []
    if not relation_family:
        reasons.append("relation_family_missing")
    if candidate_quality == "insufficient_evidence" or evidence["evidence_slot_count"] <= 0:
        reasons.append("insufficient_evidence")
    if _clean(candidate.get("source_scope")) not in {"", "current_input_only"}:
        reasons.append("non_current_input_scope")
    if evidence["requires_external_knowledge"]:
        reasons.append("external_knowledge_required")
    if evidence["requires_user_history"]:
        reasons.append("user_history_required_for_insight")
    if surface_permission and surface_permission.get("must_use_soft_expression") is not True:
        reasons.append("soft_expression_not_required_by_candidate")
    if surface_permission and surface_permission.get("must_not_surface_as_fact") is not True:
        reasons.append("fact_assertion_not_forbidden_by_candidate")
    if not {"diagnosis", "personality_claim", "cause_claim_without_evidence", "advice"}.issubset(set(forbidden_claims)):
        reasons.append("forbidden_claim_policy_incomplete")
    if material_quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED:
        reasons.append("safety_adjacent_insight_surface_blocked")

    if _flag_true(
        surface_candidate_meta,
        (
            "user_dictionary_used_as_fact",
            "user_dictionary_fact_claim",
            "asserted_from_user_dictionary",
            "user_history_used_as_fact",
            "period_tendency_from_user_dictionary",
        ),
    ) or _flag_true(
        user_dictionary_meta,
        (
            "user_dictionary_used_as_fact",
            "user_dictionary_fact_claim",
            "asserted_from_user_dictionary",
            "user_history_used_as_fact",
            "period_tendency_from_user_dictionary",
        ),
    ):
        reasons.append("user_dictionary_fact_claim_blocked")

    reasons.extend(
        _surface_rejection_reasons(
            surface=proposed_surface,
            relation_family=relation_family,
            material_quality=material_quality,
            strict_context_reasons=strict_context,
        )
    )

    if proposed_surface and _flag_true(surface_candidate_meta, ("hard_statement", "fact_assertion", "cause_claim", "diagnosis_claim", "personality_claim")):
        reasons.append("surface_candidate_meta_hard_claim_blocked")
    if proposed_surface and _flag_true(surface_candidate_meta, ("soft_expression_missing",)):
        reasons.append("soft_expression_missing")

    reasons = _dedupe(reasons)
    passed = not reasons
    return {
        "candidate_id": candidate_id,
        "relation_family": relation_family,
        "candidate_quality": candidate_quality,
        "evidence_slot_count": evidence["evidence_slot_count"],
        "source_field_ids": list(evidence["source_field_ids"]),
        "strict_gate_context_reasons": list(strict_context),
        "strict_gate_context": bool(strict_context),
        "surface_candidate_evaluated": bool(proposed_surface),
        "soft_expression_required": True,
        "soft_expression_marker_detected": bool(_SOFT_MARKER_RE.search(proposed_surface)) if proposed_surface else False,
        "passed": bool(passed),
        "blocked": not bool(passed),
        "may_surface_after_structure_insight_gate": bool(passed),
        "public_surface_connected": False,
        "surface_connection_deferred_to_phase10": bool(passed),
        "rejection_reasons": reasons,
    }


def build_structure_insight_gate_report(
    structure_insight_candidate_material: EmlisStructureInsightCandidateMaterial | Mapping[str, Any] | None = None,
    *,
    current_input: Any = None,
    proposed_surface: Any = "",
    candidate_surface: Any = "",
    surface_candidate_meta: Mapping[str, Any] | None = None,
    user_dictionary_meta: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Evaluate whether Structure Insight candidates may proceed to surface.

    ``proposed_surface`` / ``candidate_surface`` are inspected only in memory so
    Phase 9 can enforce soft-expression and forbidden-claim boundaries.  The
    returned report keeps only reason codes and counts.
    """

    material_meta = _coerce_candidate_material_meta(
        structure_insight_candidate_material,
        current_input=current_input,
        run_id=run_id,
    )
    surface = _clean(candidate_surface) or _clean(proposed_surface)
    candidate_meta = _safe_mapping(surface_candidate_meta)
    dictionary_meta = _safe_mapping(user_dictionary_meta)
    material_quality = _clean(material_meta.get("material_quality"))
    candidates = [_safe_mapping(candidate) for candidate in _listify(material_meta.get("candidates") or []) if _safe_mapping(candidate)]

    candidate_results = [
        _candidate_gate_result(
            candidate=candidate,
            material_quality=material_quality,
            proposed_surface=surface,
            surface_candidate_meta=candidate_meta,
            user_dictionary_meta=dictionary_meta,
        )
        for candidate in candidates
    ]
    reason_counts = Counter(
        reason for result in candidate_results for reason in _dedupe(result.get("rejection_reasons") or [])
    )
    blocked_results = [result for result in candidate_results if result.get("blocked")]
    allowed_results = [result for result in candidate_results if result.get("passed")]
    strict_results = [result for result in candidate_results if result.get("strict_gate_context")]

    if not candidates and material_quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED:
        reason_counts["safety_adjacent_insight_surface_blocked"] += 1

    no_candidate_safe = not candidates and material_quality != MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
    passed = bool(allowed_results) and not blocked_results or no_candidate_safe
    action = (
        GATE_ACTION_NO_CANDIDATE
        if not candidates
        else GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE
        if passed
        else GATE_ACTION_BLOCK_SURFACE_CANDIDATE
    )
    report: dict[str, Any] = {
        "version": STRUCTURE_INSIGHT_GATE_VERSION,
        "schema_version": STRUCTURE_INSIGHT_GATE_VERSION,
        "scorecard_fields_version": STRUCTURE_INSIGHT_GATE_FIELDS_VERSION,
        "source": STRUCTURE_INSIGHT_GATE_SOURCE,
        "step": STRUCTURE_INSIGHT_GATE_PHASE9_STEP,
        "source_step": STRUCTURE_INSIGHT_GATE_PHASE9_STEP,
        "phase9_structure_insight_gate_ready": True,
        "structure_insight_gate_ready": True,
        "structure_insight_candidate_version": _clean(material_meta.get("version")) or STRUCTURE_INSIGHT_CANDIDATE_VERSION,
        "structure_insight_candidate_connected": bool(material_meta.get("structure_insight_candidate_ready") or candidates),
        "structure_insight_gate_material_kind": "meta_only_gate_report",
        "run_id": _clean(run_id),
        "evaluated": True,
        "passed": bool(passed),
        "blocked": not bool(passed),
        "action": action,
        "candidate_count": len(candidates),
        "allowed_candidate_count": len(allowed_results) if candidates else 0,
        "blocked_candidate_count": len(blocked_results),
        "strict_gate_candidate_count": len(strict_results),
        "strict_gate_context_reasons": _dedupe(
            reason for result in strict_results for reason in _dedupe(result.get("strict_gate_context_reasons") or [])
        ),
        "candidate_gate_results": candidate_results,
        "allowed_candidate_ids": [str(result.get("candidate_id")) for result in allowed_results],
        "blocked_candidate_ids": [str(result.get("candidate_id")) for result in blocked_results],
        "blocked_relation_families": _dedupe(result.get("relation_family") for result in blocked_results),
        "rejection_reasons": sorted(reason_counts),
        "rejection_reason_counts": dict(reason_counts),
        "surface_candidate_evaluated": bool(surface),
        "soft_expression_required": True,
        "soft_expression_required_enforced": True,
        "soft_expression_marker_detected": bool(_SOFT_MARKER_RE.search(surface)) if surface else False,
        "soft_expression_missing_blocked": "soft_expression_missing" in reason_counts,
        "unsafe_insight_surface_blocked": any(
            reason in reason_counts
            for reason in (
                "diagnosis_surface",
                "personality_claim_surface",
                "cause_claim_without_evidence_surface",
                "advice_surface",
                "target_judgement_agreement_surface",
                "opponent_intent_claim_surface",
                "self_denial_identity_claim_as_fact_surface",
                "safety_adjacent_insight_surface_blocked",
                "user_dictionary_fact_claim_blocked",
            )
        ),
        "single_record_period_tendency_blocked": "period_tendency_from_single_record_surface" in reason_counts,
        "user_dictionary_fact_claim_blocked": "user_dictionary_fact_claim_blocked" in reason_counts,
        "anger_or_boundary_strict_gate_active": "anger_or_boundary_strict_context" in _dedupe(
            reason for result in strict_results for reason in _dedupe(result.get("strict_gate_context_reasons") or [])
        ),
        "self_denial_strict_gate_active": "self_denial_strict_context" in _dedupe(
            reason for result in strict_results for reason in _dedupe(result.get("strict_gate_context_reasons") or [])
        ),
        "safety_adjacent_strict_gate_active": bool(
            material_quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
            or "safety_adjacent_insight_surface_blocked" in reason_counts
        ),
        "public_surface_connected": False,
        "surface_connection_deferred_to_phase10": bool(passed and candidates),
        "phase9_completion_conditions": {
            "unsafe_insight_not_surface_allowed": bool(not passed or not report_has_unsafe_reason(reason_counts)),
            "soft_expression_required_enforced": True,
            "gate_not_relaxed": True,
            "public_response_shape_unchanged": True,
            "comment_text_not_written": True,
        },
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "candidate_surface_generated": False,
        "candidate_body_generated": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_gate": False,
        "comment_text_written_by_candidate": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "public_payload_changed": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "diagnosis_allowed": False,
        "personality_claim_allowed": False,
        "cause_claim_allowed": False,
        "advice_allowed": False,
        "target_judgement_agreement_allowed": False,
        "period_tendency_from_single_record_allowed": False,
        "user_dictionary_fact_claim_allowed": False,
    }
    assert_structure_insight_gate_meta_only(report)
    return report


def report_has_unsafe_reason(reason_counts: Mapping[str, Any]) -> bool:
    return any(
        reason in reason_counts
        for reason in (
            "diagnosis_surface",
            "personality_claim_surface",
            "cause_claim_without_evidence_surface",
            "advice_surface",
            "target_judgement_agreement_surface",
            "opponent_intent_claim_surface",
            "self_denial_identity_claim_as_fact_surface",
            "safety_adjacent_insight_surface_blocked",
            "user_dictionary_fact_claim_blocked",
        )
    )


def normalize_structure_insight_gate_to_scorecard_fields(
    gate_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = _safe_mapping(gate_report)
    if not data:
        data = build_structure_insight_gate_report({})
    assert_structure_insight_gate_meta_only(data)
    fields = {
        "structure_insight_gate_version": _clean(data.get("version")) or STRUCTURE_INSIGHT_GATE_VERSION,
        "structure_insight_gate_step": _clean(data.get("step")) or STRUCTURE_INSIGHT_GATE_PHASE9_STEP,
        "phase9_structure_insight_gate_ready": bool(data.get("phase9_structure_insight_gate_ready")),
        "structure_insight_gate_ready": bool(data.get("structure_insight_gate_ready")),
        "structure_insight_gate_passed": bool(data.get("passed")),
        "structure_insight_gate_blocked": bool(data.get("blocked")),
        "structure_insight_gate_action": _clean(data.get("action")),
        "structure_insight_gate_candidate_count": _int(data.get("candidate_count")),
        "structure_insight_gate_allowed_candidate_count": _int(data.get("allowed_candidate_count")),
        "structure_insight_gate_blocked_candidate_count": _int(data.get("blocked_candidate_count")),
        "structure_insight_gate_strict_gate_candidate_count": _int(data.get("strict_gate_candidate_count")),
        "structure_insight_gate_rejection_reasons": list(data.get("rejection_reasons") or []),
        "structure_insight_gate_rejection_reason_counts": dict(data.get("rejection_reason_counts") or {}),
        "structure_insight_gate_soft_expression_required_enforced": bool(data.get("soft_expression_required_enforced")),
        "structure_insight_gate_soft_expression_missing_blocked": bool(data.get("soft_expression_missing_blocked")),
        "structure_insight_gate_unsafe_insight_surface_blocked": bool(data.get("unsafe_insight_surface_blocked")),
        "structure_insight_gate_single_record_period_tendency_blocked": bool(data.get("single_record_period_tendency_blocked")),
        "structure_insight_gate_user_dictionary_fact_claim_blocked": bool(data.get("user_dictionary_fact_claim_blocked")),
        "structure_insight_gate_public_surface_connected": False,
        "structure_insight_gate_surface_connection_deferred_to_phase10": bool(
            data.get("surface_connection_deferred_to_phase10")
        ),
        "structure_insight_gate_raw_text_included": False,
        "structure_insight_gate_comment_text_body_included": False,
        "structure_insight_gate_public_response_key_added": False,
        "structure_insight_gate_response_shape_changed": False,
        "structure_insight_gate_rn_visible_contract_changed": False,
        "structure_insight_gate_gate_relaxed": False,
        "structure_insight_gate_product_gate_ready": False,
        "structure_insight_gate_public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_structure_insight_gate_meta_only(fields)
    return fields


def structure_insight_gate_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _safe_mapping(value)
    if not source:
        return {}
    if _source_has_unsafe_flags(source):
        return {
            "evaluated": True,
            "passed": False,
            "blocked": True,
            "rejection_reasons": ["structure_insight_gate_public_meta_unsafe"],
            "public_meta_summary_only": True,
        }
    summary: dict[str, Any] = {}
    for key in (
        "evaluated",
        "passed",
        "blocked",
        "soft_expression_required_enforced",
        "soft_expression_missing_blocked",
        "unsafe_insight_surface_blocked",
        "single_record_period_tendency_blocked",
        "user_dictionary_fact_claim_blocked",
        "public_surface_connected",
        "surface_connection_deferred_to_phase10",
    ):
        if isinstance(source.get(key), bool):
            summary[key] = bool(source.get(key))
    for key in ("action",):
        value_text = _clean(source.get(key))
        if value_text:
            summary[key] = value_text
    for key in ("candidate_count", "allowed_candidate_count", "blocked_candidate_count"):
        summary[key] = _int(source.get(key))
    reasons = _dedupe(source.get("rejection_reasons") or [])
    if reasons:
        summary["rejection_reasons"] = reasons[:20]
    if summary:
        summary["public_meta_summary_only"] = True
    assert_structure_insight_gate_meta_only(summary)
    return summary


def _source_has_unsafe_flags(value: Mapping[str, Any]) -> bool:
    return any(value.get(flag) is True for flag in _FORBIDDEN_TRUE_FLAGS)


def assert_structure_insight_gate_meta_only(
    value: Any,
    *,
    source: str = "structure_insight_gate",
) -> None:
    if _contains_text_payload_key(value):
        raise ValueError(f"{source}: raw input/comment/surface payload key must not be retained")
    if isinstance(value, Mapping):
        for flag in _FORBIDDEN_TRUE_FLAGS:
            if value.get(flag) is True:
                raise ValueError(f"{source}: forbidden true flag {flag}")
        for item in value.values():
            assert_structure_insight_gate_meta_only(item, source=source)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_structure_insight_gate_meta_only(item, source=source)
    json.dumps(value, ensure_ascii=False, sort_keys=True)


def dump_structure_insight_gate_report(gate_report: Mapping[str, Any] | None = None) -> str:
    data = dict(gate_report or build_structure_insight_gate_report({}))
    assert_structure_insight_gate_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "STRUCTURE_INSIGHT_GATE_VERSION",
    "STRUCTURE_INSIGHT_GATE_FIELDS_VERSION",
    "STRUCTURE_INSIGHT_GATE_PHASE9_STEP",
    "STRUCTURE_INSIGHT_GATE_STEP",
    "STRUCTURE_INSIGHT_GATE_SOURCE",
    "GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE",
    "GATE_ACTION_BLOCK_SURFACE_CANDIDATE",
    "GATE_ACTION_NO_CANDIDATE",
    "assert_structure_insight_gate_meta_only",
    "build_structure_insight_gate_report",
    "normalize_structure_insight_gate_to_scorecard_fields",
    "structure_insight_gate_public_summary",
    "dump_structure_insight_gate_report",
]
