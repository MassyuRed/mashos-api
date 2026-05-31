# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-3 observation eligibility router for EmlisAI.

The router converts the Phase20-3 input material bundle into the Phase20-1
internal response contract.  It is internal-only and does not change public
``observation_status`` keys or RN production behavior.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_input_material_bundle import (
    EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY,
    EmlisInputMaterialBundle,
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    assert_emlis_input_material_bundle_meta_contract,
    build_emlis_input_material_bundle,
)
from emlis_ai_response_contract import (
    EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY,
    ResponseKind,
    assert_internal_response_contract,
    build_emlis_internal_response_contract,
    public_input_feedback_allowed_for_response_kind,
    public_observation_status_for_response_kind,
    comment_text_required_for_response_kind,
    grounding_scope_for_response_kind,
    response_kind_for_safety_triage_kind,
)
from emlis_ai_safety_triage import (
    EmlisSafetyTriageDecision,
    TRIAGE_SAFE_OBSERVATION,
)

EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SCHEMA_VERSION: Final = "cocolon.emlis.observation_eligibility_router.v1"
EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SOURCE_PHASE: Final = "Phase20-3_Observation_Eligibility_Router"
EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY: Final = "phase20_3_observation_eligibility_router"
EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_META_KEY: Final = EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "memo",
        "memo_action",
        "thought_text",
        "action_text",
        "raw_input",
        "raw_text",
        "source_text",
        "input_text",
        "user_input",
        "current_input",
        "comment_text",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "surface_text",
        "realized_text",
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
        "public_response_key_added",
        "public_response_key_change",
        "public_status_extended",
        "observation_status_enum_extended",
        "api_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "fixed_fallback_used",
        "case_id_runtime_condition_used",
        "phase_name_runtime_condition_used",
        "phase19_case_specific_route_used",
    }
)
_SPACE_RE: Final = re.compile(r"\s+")


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def response_kind_for_material_quality(
    material_quality: Any,
    safety_triage_kind: Any = TRIAGE_SAFE_OBSERVATION,
) -> str:
    safety_kind = _clean(safety_triage_kind) or TRIAGE_SAFE_OBSERVATION
    if safety_kind != TRIAGE_SAFE_OBSERVATION:
        return response_kind_for_safety_triage_kind(safety_kind)
    quality = _clean(material_quality)
    if quality == MATERIAL_QUALITY_LOW_INFORMATION:
        return ResponseKind.LOW_INFORMATION_OBSERVATION.value
    if quality == MATERIAL_QUALITY_LIMITED_GROUNDING:
        return ResponseKind.LIMITED_GROUNDING_OBSERVATION.value
    if quality == MATERIAL_QUALITY_ELIGIBLE:
        return ResponseKind.NORMAL_OBSERVATION.value
    if quality == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED:
        return ResponseKind.SAFETY_SUPPORT_REQUIRED.value
    raise ValueError(f"unsupported material_quality: {quality or '<empty>'}")


@dataclass(frozen=True)
class EmlisObservationEligibilityRoute:
    response_kind: str
    material_quality: str
    safety_triage_kind: str
    visible_material_slots: tuple[str, ...] = field(default_factory=tuple)
    unknown_slots: tuple[str, ...] = field(default_factory=tuple)
    generic_relation_material_ids: tuple[str, ...] = field(default_factory=tuple)
    input_material_bundle_meta: Mapping[str, Any] = field(default_factory=dict)
    internal_response_contract: Mapping[str, Any] = field(default_factory=dict)
    primary_reason: str = "phase20_3_material_quality_router"
    schema_version: str = EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SCHEMA_VERSION
    source_phase: str = EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SOURCE_PHASE

    @property
    def public_observation_status(self) -> str:
        return public_observation_status_for_response_kind(self.response_kind)

    @property
    def comment_text_required(self) -> bool:
        return comment_text_required_for_response_kind(self.response_kind)

    @property
    def public_input_feedback_allowed(self) -> bool:
        return public_input_feedback_allowed_for_response_kind(self.response_kind)

    @property
    def grounding_scope(self) -> str:
        return grounding_scope_for_response_kind(self.response_kind)

    def as_meta(self) -> dict[str, Any]:
        input_meta = dict(self.input_material_bundle_meta or {})
        contract = dict(self.internal_response_contract or {})
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "source_phase": self.source_phase,
            "observation_eligibility_router_ready": True,
            "phase20_3_observation_eligibility_router_ready": True,
            "response_kind": self.response_kind,
            "material_quality": self.material_quality,
            "safety_triage_kind": self.safety_triage_kind,
            "public_observation_status": self.public_observation_status,
            "comment_text_required": self.comment_text_required,
            "public_input_feedback_allowed": self.public_input_feedback_allowed,
            "grounding_scope": self.grounding_scope,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "relation_material_ids": list(self.generic_relation_material_ids),
            "primary_reason": self.primary_reason,
            EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY: input_meta,
            "phase20_3_input_material_bundle": input_meta,
            EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: contract,
            "phase20_3_short_text_can_use_emotion_category_material": True,
            "phase20_3_low_information_is_bundle_material_shortage": True,
            "phase20_3_phase19_cd_specific_cues_runtime_disabled": True,
            "phase19_case_specific_route_used": False,
            "phase19_case_route_used": False,
            "case_specific_route_used": False,
            "a_low_information_case_route_used": False,
            "c_d_specific_runtime_cue_used": False,
            "case_id_runtime_condition_used": False,
            "phase_name_runtime_condition_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "fixed_fallback_used": False,
            "public_response_key_change": False,
            "public_response_key_added": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_emlis_observation_eligibility_route_contract(meta)
        return meta

    def as_low_information_repair_context(
        self,
        *,
        complete_initial_default_requested: bool,
    ) -> dict[str, Any]:
        """Return Step10 repair context without Phase19 compact-signal ownership.

        Phase20-3 allows low-information repair only when the input material
        bundle itself is low-information and safe for normal observation.  The
        context intentionally keeps the old Step10 key shape minimal so the
        repair integration can be migrated without public contract changes.
        """

        allowed = bool(
            complete_initial_default_requested
            and self.material_quality == MATERIAL_QUALITY_LOW_INFORMATION
            and self.response_kind == ResponseKind.LOW_INFORMATION_OBSERVATION.value
            and self.safety_triage_kind == TRIAGE_SAFE_OBSERVATION
            and self.public_input_feedback_allowed
        )
        block_reason = ""
        if not complete_initial_default_requested:
            block_reason = "complete_initial_default_not_requested"
        elif self.safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
            block_reason = "safety_triage_owns_response_kind"
        elif self.material_quality != MATERIAL_QUALITY_LOW_INFORMATION:
            block_reason = "material_quality_not_low_information"
        elif self.response_kind != ResponseKind.LOW_INFORMATION_OBSERVATION.value:
            block_reason = "response_kind_not_low_information_observation"
        return {
            "schema_version": self.schema_version,
            "source_phase": self.source_phase,
            "repair_context_source": "phase20_3_material_quality_router",
            "repair_allowed_under_complete_initial": allowed,
            "repair_block_reason": block_reason,
            "complete_initial_default_requested": bool(complete_initial_default_requested),
            "material_quality": self.material_quality,
            "response_kind": self.response_kind,
            "safety_triage_kind": self.safety_triage_kind,
            "public_observation_status": self.public_observation_status,
            "public_input_feedback_allowed": self.public_input_feedback_allowed,
            "comment_text_required": self.comment_text_required,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY: dict(self.input_material_bundle_meta or {}),
            "phase20_3_input_material_bundle": dict(self.input_material_bundle_meta or {}),
            EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: dict(self.internal_response_contract or {}),
            "phase20_3_material_quality_router_used": True,
            "phase20_3_low_information_repair_context": True,
            "phase19_compact_signal_used": False,
            "a_low_information_case_route_used": False,
            "case_specific_route_used": False,
            "phase19_case_specific_route_used": False,
            "c_d_specific_runtime_cue_used": False,
            "case_id_runtime_condition_used": False,
            "phase_name_runtime_condition_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "fixed_fallback_used": False,
            "public_response_key_change": False,
            "public_response_key_added": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }


def route_emlis_observation_eligibility_by_material(
    current_input: Any,
    *,
    safety_triage_decision: EmlisSafetyTriageDecision | Mapping[str, Any] | None = None,
    input_material_bundle: EmlisInputMaterialBundle | None = None,
) -> EmlisObservationEligibilityRoute:
    bundle = input_material_bundle or build_emlis_input_material_bundle(
        current_input,
        safety_triage_decision=safety_triage_decision,
    )
    response_kind = response_kind_for_material_quality(
        bundle.material_quality,
        bundle.safety_triage_kind,
    )
    contract = build_emlis_internal_response_contract(
        response_kind=response_kind,
        reason="phase20_3_material_quality_router",
    )
    return EmlisObservationEligibilityRoute(
        response_kind=response_kind,
        material_quality=bundle.material_quality,
        safety_triage_kind=bundle.safety_triage_kind,
        visible_material_slots=tuple(bundle.visible_material_slots),
        unknown_slots=tuple(bundle.unknown_slots),
        generic_relation_material_ids=tuple(bundle.generic_relation_material_ids),
        input_material_bundle_meta=bundle.as_meta(),
        internal_response_contract=contract,
    )


def build_emlis_observation_eligibility_route_meta(
    current_input: Any,
    *,
    safety_triage_decision: EmlisSafetyTriageDecision | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return route_emlis_observation_eligibility_by_material(
        current_input,
        safety_triage_decision=safety_triage_decision,
    ).as_meta()


def assert_emlis_observation_eligibility_route_contract(meta: Mapping[str, Any]) -> None:
    if meta.get("schema_version") != EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SCHEMA_VERSION:
        raise ValueError("unexpected observation eligibility route schema version")
    if meta.get("source_phase") != EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SOURCE_PHASE:
        raise ValueError("unexpected observation eligibility route source phase")
    if meta.get("observation_eligibility_router_ready") is not True:
        raise ValueError("observation eligibility router meta must be ready")
    contract = meta.get(EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY)
    if not isinstance(contract, Mapping):
        raise ValueError("observation eligibility route missing internal response contract")
    assert_internal_response_contract(contract)
    input_meta = meta.get(EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY)
    if not isinstance(input_meta, Mapping):
        raise ValueError("observation eligibility route missing input material bundle meta")
    assert_emlis_input_material_bundle_meta_contract(input_meta)
    if meta.get("response_kind") != contract.get("response_kind"):
        raise ValueError("route response_kind must match internal response contract")
    if meta.get("public_observation_status") != contract.get("public_observation_status"):
        raise ValueError("route public status must match internal response contract")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"forbidden true flag in observation eligibility route: {flag}")
    for key in _TEXT_PAYLOAD_KEYS:
        if key in meta:
            raise ValueError(f"raw text payload key is not allowed in observation eligibility route: {key}")
    if _contains_text_payload_key(meta):
        raise ValueError("observation eligibility route must not contain raw text payload keys")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


def route_emlis_observation_material_eligibility(
    current_input: Any,
    *,
    safety_triage_decision: EmlisSafetyTriageDecision | Mapping[str, Any] | None = None,
    input_material_bundle: EmlisInputMaterialBundle | None = None,
) -> EmlisObservationEligibilityRoute:
    return route_emlis_observation_eligibility_by_material(
        current_input,
        safety_triage_decision=safety_triage_decision,
        input_material_bundle=input_material_bundle,
    )


def assert_emlis_observation_eligibility_route_meta(meta: Mapping[str, Any]) -> None:
    assert_emlis_observation_eligibility_route_contract(meta)


def attach_phase20_3_observation_eligibility_route_meta(
    meta: Mapping[str, Any] | dict[str, Any],
    route: EmlisObservationEligibilityRoute | Mapping[str, Any],
) -> dict[str, Any]:
    out = dict(meta or {})
    route_meta = route.as_meta() if isinstance(route, EmlisObservationEligibilityRoute) else dict(route or {})
    out[EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY] = route_meta
    out[EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_META_KEY] = route_meta
    return out



__all__ = [
    "EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY",
    "EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_META_KEY",
    "EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SCHEMA_VERSION",
    "EMLIS_OBSERVATION_ELIGIBILITY_ROUTE_SOURCE_PHASE",
    "EmlisObservationEligibilityRoute",
    "assert_emlis_observation_eligibility_route_meta",
    "assert_emlis_observation_eligibility_route_contract",
    "attach_phase20_3_observation_eligibility_route_meta",
    "build_emlis_observation_eligibility_route_meta",
    "response_kind_for_material_quality",
    "route_emlis_observation_eligibility_by_material",
    "route_emlis_observation_material_eligibility",
]
