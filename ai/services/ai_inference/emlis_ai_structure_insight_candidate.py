# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 7 internal Structure Insight candidate material for EmlisAI.

This module turns the current self-report material into relation-candidate
metadata.  It deliberately does not create a visible surface, does not write
``comment_text``, does not expose raw user input, and does not add public API or
RN response keys.  The material is intended for later Structure Insight Gate /
Blind QA work, where each candidate can be checked before any surface is
allowed.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_input_material_bundle import (
    EmlisInputMaterialBundle,
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    VISIBLE_SLOT_ACTION,
    VISIBLE_SLOT_CHANGE,
    VISIBLE_SLOT_EMOTION_DIRECTION,
    VISIBLE_SLOT_EVENT,
    VISIBLE_SLOT_RELATIONSHIP,
    VISIBLE_SLOT_UNRESOLVED_WEIGHT,
    VISIBLE_SLOT_VALUE,
    build_emlis_input_material_bundle,
)
from emlis_ai_observation_structure_material_service import (
    ObservationStructureMaterial,
    build_observation_structure_material,
    observation_structure_material_forward_meta,
)

STRUCTURE_INSIGHT_CANDIDATE_VERSION: Final = "cocolon.emlis.structure_insight_candidate.v1"
STRUCTURE_INSIGHT_CANDIDATE_FIELDS_VERSION: Final = "cocolon.emlis.structure_insight_candidate.scorecard_fields.v1"
STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP: Final = "Phase7_Structure_Insight_Candidate_Internal_Material"
STRUCTURE_INSIGHT_CANDIDATE_STEP: Final = STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP
STRUCTURE_INSIGHT_CANDIDATE_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase7_StructureInsightCandidate"
STRUCTURE_INSIGHT_CANDIDATE_META_KEY: Final = "structure_insight_candidate"

RELATION_EVENT_REACTION_LINK: Final = "event_reaction_link"
RELATION_DESIRE_BLOCKAGE_CONFLICT: Final = "desire_blockage_conflict"
RELATION_EFFORT_RESIDUE: Final = "effort_residue"
RELATION_VALUE_LINE_CROSSED: Final = "value_line_crossed"
RELATION_FEAR_LOAD_PAIR: Final = "fear_load_pair"
RELATION_POSITIVE_CHANGE_RECOVERY: Final = "positive_change_recovery"
RELATION_SELF_DENIAL_IDENTITY_SPLIT: Final = "self_denial_identity_split"
RELATION_UNCERTAINTY_EFFORT_PAIR: Final = "uncertainty_effort_pair"
RELATION_MIXED_EMOTION_COEXISTENCE: Final = "mixed_emotion_coexistence"
RELATION_LONG_ARC_MULTIPLE_CORE: Final = "long_arc_multiple_core"
RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT: Final = "low_information_unspecified_weight"

RELATION_CANDIDATE_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_EVENT_REACTION_LINK,
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_EFFORT_RESIDUE,
    RELATION_VALUE_LINE_CROSSED,
    RELATION_FEAR_LOAD_PAIR,
    RELATION_POSITIVE_CHANGE_RECOVERY,
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    RELATION_UNCERTAINTY_EFFORT_PAIR,
    RELATION_MIXED_EMOTION_COEXISTENCE,
    RELATION_LONG_ARC_MULTIPLE_CORE,
    RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
)

FORBIDDEN_CLAIMS_BASE: Final[tuple[str, ...]] = (
    "diagnosis",
    "personality_claim",
    "cause_claim_without_evidence",
    "advice",
    "target_judgement_agreement",
    "period_tendency_from_single_record",
)
GATE_REQUIRED_BASE: Final[tuple[str, ...]] = (
    "evidence_boundary_gate",
    "soft_inference_surface_gate",
    "visible_surface_acceptance_gate",
    "public_meta_sanitizer",
)
SOFT_SURFACE_MARKERS: Final[tuple[str, ...]] = (
    "ように見えます",
    "かもしれません",
    "ではないでしょうか",
    "重なっているように見えます",
    "として残っているのかもしれません",
)
MUST_NOT_SURFACE_AS: Final[tuple[str, ...]] = (
    "fact_assertion",
    "diagnosis",
    "personality",
    "cause",
    "advice",
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
    "period_tendency_from_single_record",
)

_SPACE_RE: Final = re.compile(r"\s+")
_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?\n]+")
_DESIRE_RE: Final = re.compile(r"(変えたい|変わりたい|進みたい|したい|なりたい|戻りたい|返していきたい|守りたい|整えたい|向き合いたい)")
_BLOCKAGE_RE: Final = re.compile(r"(できない|出来ない|動けない|変えられない|止まって|停滞|このまま|詰ま|ぶつか|無理|限界|届かない)")
_EFFORT_RE: Final = re.compile(r"(頑張|努力|向き合|試し|続け|言葉にして|考えよう|悩んで|やってみ|耐え|我慢)")
_RESIDUE_RE: Final = re.compile(r"(疲れ|しんど|つら|重い|消耗|残って|残り|残る|引っかか|ひっかか|余韻)")
_VALUE_LINE_RE: Final = re.compile(r"(大事|大切|軽く扱|境界|線|傷つ|傷付|許せない|嫌だった|不快|怒|距離を取りたい|踏まれ)")
_FEAR_RE: Final = re.compile(r"(不安|怖|こわ|恐|大丈夫かな|心配|焦り|焦る)")
_POSITIVE_RE: Final = re.compile(r"(嬉|うれし|安心|ほっと|良かった|よかった|できた|出来た|回復|変化|進歩|達成|戻って|動いた)")
_SELF_DENIAL_RE: Final = re.compile(r"(自分が嫌|自分なんて|何もできない|なにもできない|ダメ|駄目|価値がない|嫌い|責め|消えたい気持ち)")
_UNCERTAINTY_RE: Final = re.compile(r"(大丈夫かな|これでいい|これで合って|わからない|分からない|どうしたら|迷|不安)")
_COEXISTENCE_RE: Final = re.compile(r"(けど|だけど|でも|一方で|同時に|嬉しいけど|安心したけど|怖いけど)")
_NEGATIVE_RE: Final = re.compile(r"(不安|怖|こわ|悲し|怒|嫌|つら|しんど|疲れ|寂し|焦|悔し)")
_EVENT_WORD_RE: Final = re.compile(r"(言われ|会っ|話し|聞い|見た|起き|任され|頼まれ|連絡|別れ|仕事|学校|職場|家族|友達|相手)")

_OBSERVATION_RELATION_TO_CANDIDATE: Final[dict[str, str]] = {
    "desire_stagnation": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "action_blocked": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "pressure_gap": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "priority_pressure": RELATION_VALUE_LINE_CROSSED,
    "load_accumulation": RELATION_EFFORT_RESIDUE,
    "repetition": RELATION_EFFORT_RESIDUE,
    "thought_action_discrepancy": RELATION_MIXED_EMOTION_COEXISTENCE,
    "emotion_nesting": RELATION_MIXED_EMOTION_COEXISTENCE,
    "self_insight_discovery": RELATION_UNCERTAINTY_EFFORT_PAIR,
    "low_information_weight": RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    "state_text_gap": RELATION_FEAR_LOAD_PAIR,
}


class StructureInsightCandidateMetaOnlyError(ValueError):
    """Raised when Phase 7 candidate material leaks text or changes contracts."""


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return _SPACE_RE.sub(" ", str(value).replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _joined_internal_text(bundle: EmlisInputMaterialBundle) -> str:
    # Internal-only matching string.  It is intentionally never returned.
    return "\n".join(part for part in (_clean(bundle.thought_text), _clean(bundle.action_text)) if part)


def _sentence_count(text: str) -> int:
    parts = [_clean(part) for part in _SENTENCE_SPLIT_RE.split(text) if _clean(part)]
    return len(parts) or (1 if _clean(text) else 0)


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


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _source_fields(bundle: EmlisInputMaterialBundle) -> list[str]:
    fields: list[str] = []
    if bundle.thought_text:
        fields.append("memo")
    if bundle.action_text:
        fields.append("memo_action")
    if bundle.emotion_labels:
        fields.append("emotion_details")
    if bundle.category_labels:
        fields.append("category")
    return _dedupe(fields)


def _material_slots(bundle: EmlisInputMaterialBundle) -> dict[str, bool]:
    return {
        "memo_present": bool(bundle.thought_text),
        "memo_action_present": bool(bundle.action_text),
        "selected_emotions_present": bool(bundle.emotion_labels),
        "emotion_details_present": bool(bundle.emotion_labels),
        "category_present": bool(bundle.category_labels),
    }


def _relation_evidence_fields(relation_family: str, bundle: EmlisInputMaterialBundle) -> list[str]:
    available = set(_source_fields(bundle))
    preferred: dict[str, tuple[str, ...]] = {
        RELATION_EVENT_REACTION_LINK: ("memo_action", "memo", "emotion_details", "category"),
        RELATION_DESIRE_BLOCKAGE_CONFLICT: ("memo", "memo_action", "emotion_details"),
        RELATION_EFFORT_RESIDUE: ("memo", "memo_action", "emotion_details"),
        RELATION_VALUE_LINE_CROSSED: ("memo", "memo_action", "emotion_details", "category"),
        RELATION_FEAR_LOAD_PAIR: ("memo", "memo_action", "emotion_details"),
        RELATION_POSITIVE_CHANGE_RECOVERY: ("memo", "memo_action", "emotion_details"),
        RELATION_SELF_DENIAL_IDENTITY_SPLIT: ("memo", "memo_action", "emotion_details"),
        RELATION_UNCERTAINTY_EFFORT_PAIR: ("memo", "memo_action", "emotion_details"),
        RELATION_MIXED_EMOTION_COEXISTENCE: ("memo", "memo_action", "emotion_details"),
        RELATION_LONG_ARC_MULTIPLE_CORE: ("memo", "memo_action", "emotion_details", "category"),
        RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT: ("memo", "emotion_details", "category"),
    }
    return [field for field in preferred.get(relation_family, ()) if field in available]


def _relation_forbidden_claims(relation_family: str) -> list[str]:
    claims = list(FORBIDDEN_CLAIMS_BASE)
    if relation_family == RELATION_SELF_DENIAL_IDENTITY_SPLIT:
        claims.extend(["identity_claim_as_fact", "self_denial_accepted_as_user_fact"])
    if relation_family == RELATION_VALUE_LINE_CROSSED:
        claims.extend(["target_attack_agreement", "opponent_intent_claim"])
    if relation_family == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT:
        claims.extend(["background_deep_reading", "unspecified_weight_as_fact"])
    if relation_family == RELATION_POSITIVE_CHANGE_RECOVERY:
        claims.append("positive_input_overweighted_as_hidden_problem")
    return _dedupe(claims)


def _detect_relation_families(bundle: EmlisInputMaterialBundle, observation_relation_ids: Sequence[str]) -> list[str]:
    text = _joined_internal_text(bundle)
    visible = set(bundle.visible_material_slots)
    families: list[str] = []
    has_event = VISIBLE_SLOT_EVENT in visible or bool(bundle.action_text) or bool(_EVENT_WORD_RE.search(text))
    has_emotion = VISIBLE_SLOT_EMOTION_DIRECTION in visible or bool(bundle.emotion_labels)
    has_action = VISIBLE_SLOT_ACTION in visible or bool(bundle.action_text)
    has_value_or_change = bool({VISIBLE_SLOT_VALUE, VISIBLE_SLOT_CHANGE}.intersection(visible))
    emotion_count = len(bundle.emotion_labels)
    compact_len = len(_SPACE_RE.sub("", text))

    if has_event and has_emotion:
        families.append(RELATION_EVENT_REACTION_LINK)
    if _DESIRE_RE.search(text) and _BLOCKAGE_RE.search(text):
        families.append(RELATION_DESIRE_BLOCKAGE_CONFLICT)
    if _EFFORT_RE.search(text) and _RESIDUE_RE.search(text):
        families.append(RELATION_EFFORT_RESIDUE)
    if (_VALUE_LINE_RE.search(text) and (VISIBLE_SLOT_RELATIONSHIP in visible or has_event or has_emotion)):
        families.append(RELATION_VALUE_LINE_CROSSED)
    if _FEAR_RE.search(text) and (has_event or _RESIDUE_RE.search(text) or has_action):
        families.append(RELATION_FEAR_LOAD_PAIR)
    if _POSITIVE_RE.search(text) and (has_event or has_action or has_value_or_change or has_emotion):
        families.append(RELATION_POSITIVE_CHANGE_RECOVERY)
    if _SELF_DENIAL_RE.search(text):
        families.append(RELATION_SELF_DENIAL_IDENTITY_SPLIT)
    if _UNCERTAINTY_RE.search(text) and (_EFFORT_RE.search(text) or has_action or _DESIRE_RE.search(text)):
        families.append(RELATION_UNCERTAINTY_EFFORT_PAIR)
    if (
        emotion_count >= 2
        or (_COEXISTENCE_RE.search(text) and (_POSITIVE_RE.search(text) or _NEGATIVE_RE.search(text)))
        or (_POSITIVE_RE.search(text) and _NEGATIVE_RE.search(text))
    ):
        families.append(RELATION_MIXED_EMOTION_COEXISTENCE)
    if compact_len >= 70 or (_sentence_count(text) >= 3 and len(_source_fields(bundle)) >= 3):
        families.append(RELATION_LONG_ARC_MULTIPLE_CORE)
    if (
        bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION
        or VISIBLE_SLOT_UNRESOLVED_WEIGHT in visible
    ):
        families.append(RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT)

    for relation_id in observation_relation_ids:
        family = _OBSERVATION_RELATION_TO_CANDIDATE.get(_clean(relation_id))
        if family:
            families.append(family)

    # Do not turn a low-information record into deep insight material.  Keep the
    # unspecified-weight candidate as the single safe candidate unless the input
    # already has enough concrete fields.
    if bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION:
        return [RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT]

    return [family for family in _dedupe(families) if family in RELATION_CANDIDATE_FAMILIES]


def _candidate_quality(relation_family: str, evidence_fields: Sequence[str]) -> str:
    count = len(evidence_fields)
    if relation_family == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT:
        return "low_information_boundary"
    if count >= 3:
        return "relation_candidate_ready_for_gate"
    if count >= 2:
        return "relation_candidate_needs_gate_review"
    return "insufficient_evidence"


def _candidate_surface_permission(relation_family: str, evidence_fields: Sequence[str]) -> dict[str, Any]:
    gate_ready = _candidate_quality(relation_family, evidence_fields) != "insufficient_evidence"
    return {
        "may_surface_now": False,
        "may_surface_after_structure_insight_gate": bool(gate_ready),
        "public_surface_connected_initially": False,
        "must_use_soft_expression": True,
        "must_not_surface_as_fact": True,
        "must_not_surface_as_personality": True,
        "must_not_surface_as_diagnosis": True,
        "must_not_surface_as_cause": True,
        "must_not_surface_as_advice": True,
        "allowed_surface_markers": list(SOFT_SURFACE_MARKERS),
        "must_not_surface_as": list(MUST_NOT_SURFACE_AS),
        "candidate_body_included": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
    }


def _build_candidate(
    *,
    relation_family: str,
    index: int,
    bundle: EmlisInputMaterialBundle,
    supporting_relation_ids: Sequence[str],
) -> dict[str, Any]:
    evidence_fields = _relation_evidence_fields(relation_family, bundle)
    inference_strength = "medium" if len(evidence_fields) >= 3 and relation_family not in {
        RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
        RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    } else "soft"
    candidate = {
        "schema_version": STRUCTURE_INSIGHT_CANDIDATE_VERSION,
        "candidate_id": f"{relation_family}_{index:03d}",
        "relation_family": relation_family,
        "source_scope": "current_input_only",
        "source_kind": "self_report_material_relation_candidate",
        "supporting_observation_relation_ids": list(supporting_relation_ids),
        "evidence": {
            "source_field_ids": list(evidence_fields),
            "evidence_slot_count": len(evidence_fields),
            "requires_external_knowledge": False,
            "requires_user_history": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "inference_strength": inference_strength,
        "candidate_quality": _candidate_quality(relation_family, evidence_fields),
        "surface_permission": _candidate_surface_permission(relation_family, evidence_fields),
        "forbidden_claims": _relation_forbidden_claims(relation_family),
        "gate_required": list(GATE_REQUIRED_BASE),
        "suggested_surface_role": "observation_insight_seed",
        "candidate_is_surface_text": False,
        "surface_text_generated": False,
        "candidate_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
        "public_surface_connected": False,
    }
    assert_structure_insight_candidate_meta_only(candidate, source=f"structure_insight_candidate.{relation_family}")
    return candidate


def _safe_observation_structure_meta(
    *,
    current_input: Any,
    observation_structure_material: ObservationStructureMaterial | Mapping[str, Any] | None,
) -> dict[str, Any]:
    if observation_structure_material is not None:
        return observation_structure_material_forward_meta(observation_structure_material)
    try:
        return observation_structure_material_forward_meta(
            build_observation_structure_material(current_input=current_input)
        )
    except Exception:
        # Phase 7 is an internal candidate material.  If the older structure
        # material builder cannot run for a caller, keep the candidate builder
        # usable from self-report material alone and expose no exception body.
        return {}


@dataclass(frozen=True)
class EmlisStructureInsightCandidateMaterial:
    """Text-free Phase 7 Structure Insight candidate material."""

    self_report_material: Mapping[str, Any]
    candidates: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    relation_candidate_families: tuple[str, ...] = field(default_factory=tuple)
    forbidden_claims: tuple[str, ...] = field(default_factory=tuple)
    source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    supporting_observation_relation_ids: tuple[str, ...] = field(default_factory=tuple)
    material_quality: str = MATERIAL_QUALITY_LOW_INFORMATION
    observation_structure_material_connected: bool = False
    state_answer_surface_contract_connected: bool = False
    run_id: str = ""
    schema_version: str = STRUCTURE_INSIGHT_CANDIDATE_VERSION
    step: str = STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP

    def as_meta(self) -> dict[str, Any]:
        counts = Counter(self.relation_candidate_families)
        gate_ready_count = sum(
            1
            for candidate in self.candidates
            if _safe_mapping(candidate).get("candidate_quality") != "insufficient_evidence"
        )
        meta: dict[str, Any] = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "scorecard_fields_version": STRUCTURE_INSIGHT_CANDIDATE_FIELDS_VERSION,
            "source": STRUCTURE_INSIGHT_CANDIDATE_SOURCE,
            "step": self.step,
            "source_step": self.step,
            "phase7_structure_insight_candidate_ready": True,
            "structure_insight_candidate_ready": True,
            "candidate_material_kind": "internal_meta_only",
            "target_step": "StructureInsight_v2_internal_candidate_material",
            "run_id": _clean(self.run_id),
            "self_report_material": dict(self.self_report_material),
            "self_report_material_connected": True,
            "input_material_bundle_connected": True,
            "observation_structure_material_connected": bool(self.observation_structure_material_connected),
            "state_answer_surface_contract_connected": bool(self.state_answer_surface_contract_connected),
            "state_answer_surface_contract_material_only": bool(self.state_answer_surface_contract_connected),
            "material_quality": self.material_quality,
            "source_scope": "current_input_only",
            "source_field_ids": list(self.source_field_ids),
            "evidence_slot_count": len(self.source_field_ids),
            "supporting_observation_relation_ids": list(self.supporting_observation_relation_ids),
            "supporting_observation_relation_count": len(self.supporting_observation_relation_ids),
            "relation_candidate_families": list(self.relation_candidate_families),
            "relation_candidate_family_counts": dict(counts),
            "candidate_count": len(self.candidates),
            "gate_ready_candidate_count": gate_ready_count,
            "surface_candidate_count": 0,
            "candidates": [dict(candidate) for candidate in self.candidates],
            "forbidden_claims": list(self.forbidden_claims),
            "forbidden_claim_count": len(self.forbidden_claims),
            "gate_required": list(GATE_REQUIRED_BASE),
            "must_use_soft_expression": True,
            "inference_strength_allowed": ["soft", "medium"],
            "initial_public_surface_connected": False,
            "public_surface_connected": False,
            "surface_connection_deferred_to_structure_insight_gate": True,
            "phase7_completion_conditions": {
                "structure_insight_candidate_meta_created": True,
                "raw_text_excluded": True,
                "forbidden_claims_attached": True,
                "public_response_shape_unchanged": True,
                "public_surface_not_connected_initially": True,
            },
            "raw_input_included": False,
            "raw_text_included": False,
            "input_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "candidate_surface_generated": False,
            "comment_text_generated": False,
            "comment_text_key_written": False,
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
            "period_tendency_from_single_record": False,
        }
        assert_structure_insight_candidate_meta_only(meta)
        return meta


def build_structure_insight_candidate_material(
    current_input: Any,
    *,
    input_material_bundle: EmlisInputMaterialBundle | Mapping[str, Any] | None = None,
    observation_structure_material: ObservationStructureMaterial | Mapping[str, Any] | None = None,
    run_id: str = "",
) -> EmlisStructureInsightCandidateMaterial:
    """Build Phase 7 internal Structure Insight candidate material.

    ``current_input`` may include raw text, but only relation ids, source-field
    ids, evidence counts, and policy flags are retained in the returned meta.
    """

    if isinstance(input_material_bundle, EmlisInputMaterialBundle):
        bundle = input_material_bundle
    else:
        bundle = build_emlis_input_material_bundle(current_input)

    source_fields = _source_fields(bundle)
    observation_meta = _safe_observation_structure_meta(
        current_input=current_input,
        observation_structure_material=observation_structure_material,
    )
    observation_relation_ids = _dedupe(
        observation_meta.get("selected_relation_ids")
        or observation_meta.get("structure_relation_ids")
        or []
    )
    relation_families = _detect_relation_families(bundle, observation_relation_ids)

    # Safety-triage material is not converted into normal Structure Insight.
    # Keep only the internally grounded self-denial identity split candidate so
    # downstream gates can attach forbidden-claim boundaries without surfacing it.
    if bundle.material_quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED:
        relation_families = (
            [RELATION_SELF_DENIAL_IDENTITY_SPLIT]
            if RELATION_SELF_DENIAL_IDENTITY_SPLIT in relation_families
            else []
        )

    supporting_by_family: dict[str, list[str]] = {}
    for relation_id in observation_relation_ids:
        family = _OBSERVATION_RELATION_TO_CANDIDATE.get(relation_id)
        if family:
            supporting_by_family.setdefault(family, []).append(relation_id)

    candidates = tuple(
        _build_candidate(
            relation_family=family,
            index=index + 1,
            bundle=bundle,
            supporting_relation_ids=supporting_by_family.get(family, []),
        )
        for index, family in enumerate(relation_families)
    )
    forbidden_claims = _dedupe(
        claim
        for candidate in candidates
        for claim in _safe_mapping(candidate).get("forbidden_claims") or []
    )
    self_report_material = {
        "schema_version": "cocolon.emlis.product_readfeel.self_report_material.v1",
        "source_kind": "current_input",
        "record_scope": "single_current_record",
        "material_slots": _material_slots(bundle),
        "material_summary": {
            "event_fact_present": VISIBLE_SLOT_EVENT in set(bundle.visible_material_slots) or bool(bundle.action_text),
            "explicit_reaction_present": bool(bundle.thought_text or bundle.emotion_labels),
            "selected_emotion_count": len(bundle.emotion_labels),
            "category_topic_count": len(bundle.category_labels),
            "unknown_slot_count": len(bundle.unknown_slots),
        },
        "source_field_ids": list(source_fields),
        "evidence_slot_count": len(source_fields),
        "material_quality": bundle.material_quality,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
    }
    material = EmlisStructureInsightCandidateMaterial(
        self_report_material=self_report_material,
        candidates=candidates,
        relation_candidate_families=tuple(relation_families),
        forbidden_claims=tuple(forbidden_claims),
        source_field_ids=tuple(source_fields),
        supporting_observation_relation_ids=tuple(observation_relation_ids),
        material_quality=bundle.material_quality,
        observation_structure_material_connected=bool(observation_meta),
        state_answer_surface_contract_connected=bool(observation_meta.get("state_answer_surface_contract_connected")),
        run_id=run_id,
    )
    assert_structure_insight_candidate_meta_only(material.as_meta())
    return material


def build_structure_insight_candidate_meta(
    current_input: Any,
    *,
    input_material_bundle: EmlisInputMaterialBundle | Mapping[str, Any] | None = None,
    observation_structure_material: ObservationStructureMaterial | Mapping[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    return build_structure_insight_candidate_material(
        current_input,
        input_material_bundle=input_material_bundle,
        observation_structure_material=observation_structure_material,
        run_id=run_id,
    ).as_meta()


def normalize_structure_insight_candidate_to_scorecard_fields(
    material: EmlisStructureInsightCandidateMaterial | Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = material.as_meta() if isinstance(material, EmlisStructureInsightCandidateMaterial) else _safe_mapping(material)
    if not data:
        data = build_structure_insight_candidate_material({}).as_meta()
    assert_structure_insight_candidate_meta_only(data, source="structure_insight_candidate_scorecard_fields_source")
    fields = {
        "structure_insight_candidate_version": _clean(data.get("version")) or STRUCTURE_INSIGHT_CANDIDATE_VERSION,
        "structure_insight_candidate_step": _clean(data.get("step")) or STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP,
        "phase7_structure_insight_candidate_ready": bool(data.get("phase7_structure_insight_candidate_ready")),
        "structure_insight_candidate_ready": bool(data.get("structure_insight_candidate_ready")),
        "structure_insight_candidate_internal_material_only": True,
        "structure_insight_candidate_count": int(data.get("candidate_count") or 0),
        "structure_insight_candidate_gate_ready_count": int(data.get("gate_ready_candidate_count") or 0),
        "structure_insight_candidate_relation_families": list(data.get("relation_candidate_families") or []),
        "structure_insight_candidate_relation_family_counts": dict(data.get("relation_candidate_family_counts") or {}),
        "structure_insight_candidate_source_field_ids": list(data.get("source_field_ids") or []),
        "structure_insight_candidate_evidence_slot_count": int(data.get("evidence_slot_count") or 0),
        "structure_insight_candidate_forbidden_claims": list(data.get("forbidden_claims") or []),
        "structure_insight_candidate_forbidden_claim_count": int(data.get("forbidden_claim_count") or 0),
        "structure_insight_candidate_must_use_soft_expression": bool(data.get("must_use_soft_expression")),
        "structure_insight_candidate_public_surface_connected": False,
        "structure_insight_candidate_surface_connection_deferred_to_gate": True,
        "structure_insight_candidate_raw_text_included": False,
        "structure_insight_candidate_comment_text_body_included": False,
        "structure_insight_candidate_public_response_key_added": False,
        "structure_insight_candidate_response_shape_changed": False,
        "structure_insight_candidate_rn_visible_contract_changed": False,
        "structure_insight_candidate_product_gate_ready": False,
        "structure_insight_candidate_public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_structure_insight_candidate_meta_only(fields, source="structure_insight_candidate_scorecard_fields")
    return fields


def assert_structure_insight_candidate_meta_only(
    value: Any,
    *,
    source: str = "structure_insight_candidate",
) -> None:
    if _contains_text_payload_key(value):
        raise StructureInsightCandidateMetaOnlyError(f"{source}: raw input/comment/candidate body key must not be retained")
    if isinstance(value, Mapping):
        for flag in _FORBIDDEN_TRUE_FLAGS:
            if value.get(flag) is True:
                raise StructureInsightCandidateMetaOnlyError(f"{source}: forbidden true flag {flag}")
        for key in ("diagnosis_allowed", "personality_claim_allowed", "cause_claim_allowed", "advice_allowed"):
            if value.get(key) is True:
                raise StructureInsightCandidateMetaOnlyError(f"{source}: unsafe insight claim is allowed")
        for item in value.values():
            assert_structure_insight_candidate_meta_only(item, source=source)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_structure_insight_candidate_meta_only(item, source=source)
    json.dumps(value, ensure_ascii=False, sort_keys=True)


def dump_structure_insight_candidate_material(
    material: EmlisStructureInsightCandidateMaterial | Mapping[str, Any] | None = None,
) -> str:
    data = material.as_meta() if isinstance(material, EmlisStructureInsightCandidateMaterial) else dict(material or {})
    if not data:
        data = build_structure_insight_candidate_material({}).as_meta()
    assert_structure_insight_candidate_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "STRUCTURE_INSIGHT_CANDIDATE_VERSION",
    "STRUCTURE_INSIGHT_CANDIDATE_FIELDS_VERSION",
    "STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP",
    "STRUCTURE_INSIGHT_CANDIDATE_STEP",
    "STRUCTURE_INSIGHT_CANDIDATE_META_KEY",
    "RELATION_EVENT_REACTION_LINK",
    "RELATION_DESIRE_BLOCKAGE_CONFLICT",
    "RELATION_EFFORT_RESIDUE",
    "RELATION_VALUE_LINE_CROSSED",
    "RELATION_FEAR_LOAD_PAIR",
    "RELATION_POSITIVE_CHANGE_RECOVERY",
    "RELATION_SELF_DENIAL_IDENTITY_SPLIT",
    "RELATION_UNCERTAINTY_EFFORT_PAIR",
    "RELATION_MIXED_EMOTION_COEXISTENCE",
    "RELATION_LONG_ARC_MULTIPLE_CORE",
    "RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT",
    "RELATION_CANDIDATE_FAMILIES",
    "EmlisStructureInsightCandidateMaterial",
    "StructureInsightCandidateMetaOnlyError",
    "assert_structure_insight_candidate_meta_only",
    "build_structure_insight_candidate_material",
    "build_structure_insight_candidate_meta",
    "normalize_structure_insight_candidate_to_scorecard_fields",
    "dump_structure_insight_candidate_material",
]
