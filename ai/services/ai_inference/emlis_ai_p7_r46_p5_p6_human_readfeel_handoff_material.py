# -*- coding: utf-8 -*-
"""P7-R46 R10/R11 body-free handoff material for P5/P6 human readfeel review.

R10/R11 do not run human review and do not materialize reviewer-facing bodies.
They prepare a release-closed, body-free handoff index that says which local
human review packets must be created outside public meta / P7 scorecard
material.

The actual reviewer packet may contain the surface a human reads.  This module
keeps that packet out of public/runtime/P7 release material and preserves the
HOLD refs until a real human review is completed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)

P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r46.p5_human_blind_qa_handoff_material.v1"
)
P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r46.p6_limited_human_readfeel_handoff_material.v1"
)
P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r46.p5_p6_human_readfeel_handoff_summary.v1"
)
P7_R46_HUMAN_READFEEL_HANDOFF_STEP: Final = (
    "R10_R11_P5P6HumanReadfeelHandoffMaterial_20260617"
)
P7_R46_HUMAN_READFEEL_RETURN_SCOPE: Final = (
    "p7_r46_p5_p6_human_readfeel_return_material_only"
)

P5_HUMAN_BLIND_QA_HOLD_REF: Final = "P7-HOLD-001"
P5_HUMAN_BLIND_QA_RETURN_HOLD_REF: Final = "HOLD-P5-001"
P6_LIMITED_HUMAN_READFEEL_HOLD_REF: Final = "P7-HOLD-002"
P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF: Final = "HOLD-P6-001"

P5_HUMAN_BLIND_QA_FAMILIES: Final[tuple[str, ...]] = (
    "history_line_eligible_input",
    "standard_state_answer_owned_history",
    "self_understanding_owned_history",
    "uncertainty_support_owned_history",
    "change_future_intention_owned_history",
    "relationship_gratitude_recovery_owned_history",
    "low_information_history_not_eligible",
    "free_tier_history_present_not_allowed",
)
P5_HUMAN_BLIND_QA_RATING_AXES: Final[tuple[str, ...]] = (
    "history_connection_naturalness",
    "creepy_absence",
    "overclaim_absence",
    "self_blame_non_amplification",
    "wants_more_input_or_accumulation",
    "non_shallow_repeat",
)
P5_HUMAN_BLIND_QA_TARGETS: Final[dict[str, float]] = {
    "history_connection_naturalness": 0.90,
    "creepy_absence": 0.95,
    "overclaim_absence": 0.95,
    "self_blame_non_amplification": 0.95,
    "wants_more_input_or_accumulation": 0.85,
    "non_shallow_repeat": 0.90,
}

P6_LIMITED_READFEEL_REVIEW_FAMILIES: Final[tuple[str, ...]] = (
    "structure_question",
    "long_meaning_arc",
    "self_understanding_follow",
)
P6_NO_CONNECT_FAMILIES: Final[tuple[str, ...]] = (
    "daily_unpleasant",
    "daily_positive",
    "positive_only",
    "low_information",
    "limited_grounding_insufficient",
    "safety_triage_required",
)
P6_LIMITED_READFEEL_RATING_AXES: Final[tuple[str, ...]] = (
    "structure_insight_candidate_quality",
    "relation_seen_feeling",
    "overclaim_absence",
    "diagnosis_absence",
    "creepy_absence",
    "advice_pressure_absence",
    "wants_more_input_or_accumulation",
)
P6_LIMITED_READFEEL_TARGETS: Final[dict[str, float]] = {
    "structure_insight_candidate_quality": 0.90,
    "relation_seen_feeling": 0.85,
    "overclaim_absence": 0.95,
    "diagnosis_absence": 1.0,
    "creepy_absence": 0.95,
    "advice_pressure_absence": 0.95,
    "wants_more_input_or_accumulation": 0.85,
}

_BODY_FREE_BOUNDARY = {
    "local_body_packet_release_material": False,
    "local_body_packet_public_meta_material": False,
    "local_body_packet_p7_scorecard_material": False,
    "public_meta_body_free_required": True,
    "scorecard_body_free_required": True,
    "release_material_body_free_required": True,
    "reviewer_payload_externalized": True,
    "actual_review_bodies_materialized_here": False,
}

_LOCAL_BODY_PACKET_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "review_surface",
        "current_input_ref",
        "current_input_for_reviewer",
        "comment_text_for_reviewer",
        "history_summary_for_reviewer",
        "insight_text_for_reviewer",
        "insight_surface_for_reviewer",
        "surface_for_reviewer",
        "visible_surface_for_reviewer",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_free_text",
        "blind_qa_free_text",
    }
)


def _contains_local_body_packet_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _LOCAL_BODY_PACKET_PAYLOAD_KEYS
            or _contains_local_body_packet_payload_key(child)
            for key, child in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_local_body_packet_payload_key(child) for child in value)
    return False


def _assert_no_local_body_packet_payload(value: Any, *, source: str) -> None:
    if _contains_local_body_packet_payload_key(value):
        raise ValueError(f"{source} contains local-only reviewer body payload keys")



def _case_ref(row: Mapping[str, Any], *, index: int, default_family: str) -> dict[str, Any]:
    data = safe_mapping(row)
    return {
        "case_ref_id": clean_identifier(
            data.get("case_ref_id") or data.get("case_id") or data.get("row_id"),
            default=f"case_{index}",
            max_length=96,
        ),
        "family": clean_identifier(data.get("family"), default=default_family, max_length=96),
        "subscription_tier": clean_identifier(data.get("subscription_tier"), default="unknown", max_length=32),
        "source_row_ref": clean_identifier(data.get("source_row_ref") or data.get("row_id"), default=f"row_{index}", max_length=96),
        "eligible": data.get("eligible") is True,
        "visible_applied": data.get("visible_applied") is True,
        "runtime_evaluated": data.get("runtime_evaluated") is True,
        "body_free": True,
    }


def _case_refs(rows: Sequence[Mapping[str, Any]] | None, *, default_family: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for index, row in enumerate(list(rows or []), start=1):
        _assert_no_local_body_packet_payload(row, source=f"p7_r46_human_readfeel.case_refs[{index}]")
        assert_p7_no_body_payload_or_contract_mutation(row, source=f"p7_r46_human_readfeel.case_refs[{index}]")
        refs.append(_case_ref(row, index=index, default_family=default_family))
    return refs


def _review_body_packet_boundary(*, packet_kind: str, external_fields: Sequence[str]) -> dict[str, Any]:
    return {
        "packet_kind": packet_kind,
        "review_scope": "local_human_review_only_not_public_meta",
        "local_body_packet_required": True,
        "local_body_packet_materialized_here": False,
        "local_body_packet_release_material": False,
        "local_body_packet_public_meta_material": False,
        "local_body_packet_p7_scorecard_material": False,
        "externalized_body_field_refs": list(external_fields),
        "reviewer_payload_externalized": True,
        "storage_and_disposal_policy_required_before_formal_run": True,
        "contains_actual_review_body_here": False,
        "contains_reviewer_free_text_here": False,
    }


def _common_boundary() -> dict[str, Any]:
    return {
        "public_contract": public_contract_flags(),
        "body_free_markers": body_free_flags(include_history=True, include_reviewer=True, include_terminal=True),
        "body_free_boundary": dict(_BODY_FREE_BOUNDARY),
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "full_backend_suite_green_claim_allowed": False,
        "real_device_modal_review_confirmed": False,
    }


def build_p5_human_blind_qa_handoff_material(
    case_refs: Sequence[Mapping[str, Any]] | None = None,
    *,
    material_id: Any = "p7_r46_p5_human_blind_qa_handoff_material",
) -> dict[str, Any]:
    """Build the R10 body-free P5 human Blind QA handoff material.

    This is an index/blueprint only.  It does not include the user's current
    input, history bodies, returned public surface, reviewer prose, or ratings.
    """

    refs = _case_refs(case_refs, default_family="history_line_eligible_input")
    unresolved_hold_refs = [P5_HUMAN_BLIND_QA_HOLD_REF, P5_HUMAN_BLIND_QA_RETURN_HOLD_REF]
    material = {
        "schema_version": P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_HUMAN_READFEEL_HANDOFF_STEP,
        "scope": P7_R46_HUMAN_READFEEL_RETURN_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_p5_human_blind_qa_handoff_material", max_length=160),
        "handoff_kind": "p5_human_blind_qa_handoff_material",
        "review_scope": "local_human_review_only_not_public_meta",
        "review_not_run": True,
        "p5_human_blind_qa_ready": True,
        "p5_human_blind_qa_confirmed": False,
        "human_review_completed": False,
        "families": list(P5_HUMAN_BLIND_QA_FAMILIES),
        "required_family_count": len(P5_HUMAN_BLIND_QA_FAMILIES),
        "rating_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
        "target_thresholds": dict(P5_HUMAN_BLIND_QA_TARGETS),
        "case_refs": refs,
        "case_ref_count": len(refs),
        "runtime_prerequisites": {
            "display_contract_green_required": True,
            "p5_major_subset_green_required": True,
            "public_meta_body_free_required": True,
            "gate_relaxation_absence_required": True,
            "free_tier_history_line_block_required": True,
            "low_information_history_line_block_required": True,
        },
        "review_body_packet_boundary": _review_body_packet_boundary(
            packet_kind="p5_human_blind_qa_local_review_packet",
            external_fields=(
                "current_input_surface_ref",
                "returned_observation_surface_ref",
                "owned_history_summary_surface_ref",
            ),
        ),
        "unresolved_hold_refs": unresolved_hold_refs,
        "hold_refs": unresolved_hold_refs,
        **_common_boundary(),
        "body_free": True,
    }
    assert_p5_human_blind_qa_handoff_material_contract(material)
    return material


def build_p6_limited_human_readfeel_handoff_material(
    case_refs: Sequence[Mapping[str, Any]] | None = None,
    *,
    material_id: Any = "p7_r46_p6_limited_human_readfeel_handoff_material",
) -> dict[str, Any]:
    """Build the R11 body-free P6 limited human readfeel review handoff material."""

    refs = _case_refs(case_refs, default_family="structure_question")
    unresolved_hold_refs = [P6_LIMITED_HUMAN_READFEEL_HOLD_REF, P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF]
    material = {
        "schema_version": P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_HUMAN_READFEEL_HANDOFF_STEP,
        "scope": P7_R46_HUMAN_READFEEL_RETURN_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_p6_limited_human_readfeel_handoff_material", max_length=160),
        "handoff_kind": "p6_limited_human_readfeel_handoff_material",
        "review_scope": "local_human_review_only_not_public_meta",
        "review_not_run": True,
        "p6_limited_human_readfeel_review_ready": True,
        "p6_human_readfeel_review_confirmed": False,
        "human_review_completed": False,
        "review_families": list(P6_LIMITED_READFEEL_REVIEW_FAMILIES),
        "no_connect_families": list(P6_NO_CONNECT_FAMILIES),
        "visible_expansion_allowed": False,
        "visible_expansion_requires_future_design": True,
        "history_used_as_fact_allowed": False,
        "p5_history_line_substitution_allowed": False,
        "rating_axes": list(P6_LIMITED_READFEEL_RATING_AXES),
        "target_thresholds": dict(P6_LIMITED_READFEEL_TARGETS),
        "case_refs": refs,
        "case_ref_count": len(refs),
        "runtime_prerequisites": {
            "display_contract_green_required": True,
            "p6_major_subset_green_required": True,
            "public_meta_body_free_required": True,
            "gate_relaxation_absence_required": True,
            "no_connect_family_block_required": True,
            "diagnosis_absence_required": True,
            "advice_pressure_absence_required": True,
        },
        "review_body_packet_boundary": _review_body_packet_boundary(
            packet_kind="p6_limited_human_readfeel_local_review_packet",
            external_fields=(
                "current_input_surface_ref",
                "returned_observation_surface_ref",
                "structure_insight_surface_position_ref",
            ),
        ),
        "unresolved_hold_refs": unresolved_hold_refs,
        "hold_refs": unresolved_hold_refs,
        **_common_boundary(),
        "body_free": True,
    }
    assert_p6_limited_human_readfeel_handoff_material_contract(material)
    return material


def build_p5_p6_human_readfeel_handoff_summary(
    *,
    p5_material: Mapping[str, Any] | None = None,
    p6_material: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r46_p5_p6_human_readfeel_handoff_summary",
) -> dict[str, Any]:
    """Build the combined R10/R11 handoff summary without promoting release/P8."""

    p5 = dict(p5_material) if p5_material is not None else build_p5_human_blind_qa_handoff_material()
    p6 = dict(p6_material) if p6_material is not None else build_p6_limited_human_readfeel_handoff_material()
    assert_p5_human_blind_qa_handoff_material_contract(p5)
    assert_p6_limited_human_readfeel_handoff_material_contract(p6)
    unresolved = dedupe_identifiers(
        [
            *dedupe_identifiers(p5.get("unresolved_hold_refs")),
            *dedupe_identifiers(p6.get("unresolved_hold_refs")),
            "P7-HOLD-003",
            "P7-HOLD-004",
        ],
        limit=20,
        max_length=80,
    )
    summary = {
        "schema_version": P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R46_HUMAN_READFEEL_HANDOFF_STEP,
        "scope": P7_R46_HUMAN_READFEEL_RETURN_SCOPE,
        "material_id": clean_identifier(material_id, default="p7_r46_p5_p6_human_readfeel_handoff_summary", max_length=160),
        "current_phase": "P7",
        "p5_material_schema_version": P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
        "p6_material_schema_version": P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
        "p5_human_blind_qa_ready": p5.get("p5_human_blind_qa_ready") is True,
        "p5_human_blind_qa_confirmed": False,
        "p6_limited_human_readfeel_review_ready": p6.get("p6_limited_human_readfeel_review_ready") is True,
        "p6_human_readfeel_review_confirmed": False,
        "human_review_not_run": True,
        "actual_review_bodies_materialized_here": False,
        "unresolved_hold_refs": unresolved,
        "hold_refs": unresolved,
        "p5_material": p5,
        "p6_material": p6,
        **_common_boundary(),
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "body_free": True,
    }
    assert_p5_p6_human_readfeel_handoff_summary_contract(summary)
    return summary


def _assert_common_contract(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    payload = safe_mapping(data)
    if payload.get("schema_version") != schema_version:
        raise ValueError(f"unexpected {source} schema_version")
    if payload.get("phase") != P7_PHASE:
        raise ValueError(f"unexpected {source} phase")
    if payload.get("step") != P7_R46_HUMAN_READFEEL_HANDOFF_STEP:
        raise ValueError(f"unexpected {source} step")
    if payload.get("release_allowed") is not False:
        raise ValueError(f"{source} must remain release-closed")
    if payload.get("p7_complete") is not False or payload.get("p8_start_allowed") is not False:
        raise ValueError(f"{source} must not mark P7 complete or P8 ready")
    if payload.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    assert_false_markers(safe_mapping(payload.get("public_contract")), source=f"{source}.public_contract")
    assert_false_markers(safe_mapping(payload.get("body_free_markers")), source=f"{source}.body_free_markers")
    _assert_no_local_body_packet_payload(payload, source=source)
    assert_p7_no_body_payload_or_contract_mutation(payload, source=source)


def _assert_review_body_packet_boundary(boundary: Mapping[str, Any], *, source: str) -> None:
    data = safe_mapping(boundary)
    if data.get("review_scope") != "local_human_review_only_not_public_meta":
        raise ValueError(f"{source} review scope changed")
    for key in (
        "local_body_packet_required",
        "reviewer_payload_externalized",
        "storage_and_disposal_policy_required_before_formal_run",
    ):
        if data.get(key) is not True:
            raise ValueError(f"{source} must keep {key}=True")
    for key in (
        "local_body_packet_materialized_here",
        "local_body_packet_release_material",
        "local_body_packet_public_meta_material",
        "local_body_packet_p7_scorecard_material",
        "contains_actual_review_body_here",
        "contains_reviewer_free_text_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")


def assert_p5_human_blind_qa_handoff_material_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_common_contract(
        data,
        schema_version=P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
        source="p7_r46_p5_human_blind_qa_handoff_material",
    )
    if data.get("review_scope") != "local_human_review_only_not_public_meta":
        raise ValueError("P5 human QA review scope changed")
    if data.get("p5_human_blind_qa_confirmed") is not False or data.get("human_review_completed") is not False:
        raise ValueError("P5 human Blind QA must not be marked complete by handoff material")
    if list(data.get("families") or []) != list(P5_HUMAN_BLIND_QA_FAMILIES):
        raise ValueError("P5 human Blind QA family set changed")
    if list(data.get("rating_axes") or []) != list(P5_HUMAN_BLIND_QA_RATING_AXES):
        raise ValueError("P5 human Blind QA rating axes changed")
    if P5_HUMAN_BLIND_QA_HOLD_REF not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=20):
        raise ValueError("P7-HOLD-001 must remain until P5 human Blind QA completes")
    _assert_review_body_packet_boundary(
        safe_mapping(data.get("review_body_packet_boundary")),
        source="p7_r46_p5_human_blind_qa_handoff_material.review_body_packet_boundary",
    )
    return True


def assert_p6_limited_human_readfeel_handoff_material_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_common_contract(
        data,
        schema_version=P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
        source="p7_r46_p6_limited_human_readfeel_handoff_material",
    )
    if data.get("review_scope") != "local_human_review_only_not_public_meta":
        raise ValueError("P6 human readfeel review scope changed")
    if data.get("p6_human_readfeel_review_confirmed") is not False or data.get("human_review_completed") is not False:
        raise ValueError("P6 human readfeel review must not be marked complete by handoff material")
    if list(data.get("review_families") or []) != list(P6_LIMITED_READFEEL_REVIEW_FAMILIES):
        raise ValueError("P6 limited review family set changed")
    if list(data.get("no_connect_families") or []) != list(P6_NO_CONNECT_FAMILIES):
        raise ValueError("P6 no-connect family set changed")
    if list(data.get("rating_axes") or []) != list(P6_LIMITED_READFEEL_RATING_AXES):
        raise ValueError("P6 limited readfeel rating axes changed")
    if data.get("visible_expansion_allowed") is not False:
        raise ValueError("P6 visible expansion cannot be enabled by R11 material")
    if data.get("history_used_as_fact_allowed") is not False:
        raise ValueError("P6 review must not allow history as fact")
    if data.get("p5_history_line_substitution_allowed") is not False:
        raise ValueError("P6 review must not substitute P5 history line")
    if P6_LIMITED_HUMAN_READFEEL_HOLD_REF not in dedupe_identifiers(data.get("unresolved_hold_refs"), limit=20):
        raise ValueError("P7-HOLD-002 must remain until P6 human readfeel review completes")
    _assert_review_body_packet_boundary(
        safe_mapping(data.get("review_body_packet_boundary")),
        source="p7_r46_p6_limited_human_readfeel_handoff_material.review_body_packet_boundary",
    )
    return True


def assert_p5_p6_human_readfeel_handoff_summary_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    _assert_common_contract(
        data,
        schema_version=P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION,
        source="p7_r46_p5_p6_human_readfeel_handoff_summary",
    )
    if data.get("current_phase") != "P7":
        raise ValueError("R10/R11 summary must keep current phase as P7")
    if data.get("p5_human_blind_qa_confirmed") is not False:
        raise ValueError("R10/R11 summary must not confirm P5 human QA")
    if data.get("p6_human_readfeel_review_confirmed") is not False:
        raise ValueError("R10/R11 summary must not confirm P6 human readfeel")
    if data.get("actual_review_bodies_materialized_here") is not False:
        raise ValueError("R10/R11 summary must not materialize review bodies")
    unresolved = set(dedupe_identifiers(data.get("unresolved_hold_refs"), limit=40))
    if {P5_HUMAN_BLIND_QA_HOLD_REF, P6_LIMITED_HUMAN_READFEEL_HOLD_REF} - unresolved:
        raise ValueError("R10/R11 summary must preserve P5/P6 unresolved HOLD refs")
    assert_p5_human_blind_qa_handoff_material_contract(safe_mapping(data.get("p5_material")))
    assert_p6_limited_human_readfeel_handoff_material_contract(safe_mapping(data.get("p6_material")))
    return True


__all__ = [
    "P5_HUMAN_BLIND_QA_FAMILIES",
    "P5_HUMAN_BLIND_QA_HOLD_REF",
    "P5_HUMAN_BLIND_QA_RETURN_HOLD_REF",
    "P5_HUMAN_BLIND_QA_RATING_AXES",
    "P6_LIMITED_HUMAN_READFEEL_HOLD_REF",
    "P6_LIMITED_HUMAN_READFEEL_RETURN_HOLD_REF",
    "P6_LIMITED_READFEEL_RATING_AXES",
    "P6_LIMITED_READFEEL_REVIEW_FAMILIES",
    "P6_NO_CONNECT_FAMILIES",
    "P7_R46_HUMAN_READFEEL_HANDOFF_STEP",
    "P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION",
    "P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION",
    "P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION",
    "assert_p5_human_blind_qa_handoff_material_contract",
    "assert_p5_p6_human_readfeel_handoff_summary_contract",
    "assert_p6_limited_human_readfeel_handoff_material_contract",
    "build_p5_human_blind_qa_handoff_material",
    "build_p5_p6_human_readfeel_handoff_summary",
    "build_p6_limited_human_readfeel_handoff_material",
]
