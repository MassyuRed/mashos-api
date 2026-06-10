# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-5 fixture connector for body-free surface signature audit.

The fixture connects P4-1 target cases, P4-2 material audit outputs, and P4-4
family policy to synthetic body-free surface signature observations.  It never
keeps synthetic input bodies, rendered Emlis ``comment_text`` bodies, raw
history material, or raw test logs.
"""

from collections.abc import Mapping
import json
from typing import Any

from emlis_ai_product_readfeel_p4_surface_signature_audit import (
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610,
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610,
    build_product_readfeel_p4_surface_signature_audit_20260610,
    build_product_readfeel_p4_surface_signature_audit_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_family_tuning_policy_20260610 import (
    build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_material_audit_20260610 import (
    build_product_readfeel_p4_material_audit_from_p4_1_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
)


def build_product_readfeel_p4_surface_signature_observations_20260610() -> dict[str, dict[str, Any]]:
    """Return body-free replay observations for P4-5 generic/repeated signatures."""

    observations = {
        "p3-daily_unpleasant-001": {
            "section_role_sequence": ["observation", "reception"],
            "opening_shape_family": "generic_reception_opening",
            "closing_shape_family": "generic_soft_closing",
            "observed_temperature_profile": "generic_reception_flattened",
            "observed_anchor_roles": ["emlis_reception_anchor"],
            "observation_anchor_count": 0,
            "reception_anchor_count": 1,
            "generic_empathy_marker_count": 2,
            "question_count": 0,
            "question_position": "none",
            "same_closing_family_repetition_count": 4,
            "same_section_role_sequence_repetition_count": 4,
            "observed_signature_cluster_size": 4,
            "mirror_only_detected": False,
            "comfort_only_surface_detected": True,
            "forbidden_surface_classes_present": ["generic_comfort_template"],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
        "p3-daily_unpleasant-002": {
            "section_role_sequence": ["observation", "reception"],
            "opening_shape_family": "generic_reception_opening",
            "closing_shape_family": "generic_soft_closing",
            "observed_temperature_profile": "generic_reception_flattened",
            "observed_anchor_roles": ["emlis_reception_anchor"],
            "observation_anchor_count": 1,
            "reception_anchor_count": 1,
            "generic_empathy_marker_count": 2,
            "question_count": 0,
            "question_position": "none",
            "same_closing_family_repetition_count": 4,
            "same_section_role_sequence_repetition_count": 4,
            "observed_signature_cluster_size": 4,
            "mirror_only_detected": True,
            "comfort_only_surface_detected": False,
            "forbidden_surface_classes_present": ["generic_comfort_template"],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
        "p3-structure_question-001": {
            "section_role_sequence": ["observation", "reception"],
            "opening_shape_family": "generic_question_opening",
            "closing_shape_family": "generic_soft_closing",
            "observed_temperature_profile": "generic_reception_flattened",
            "observed_anchor_roles": ["emlis_reception_anchor"],
            "observation_anchor_count": 1,
            "reception_anchor_count": 0,
            "generic_empathy_marker_count": 1,
            "question_count": 1,
            "question_position": "before_reception",
            "same_closing_family_repetition_count": 3,
            "same_section_role_sequence_repetition_count": 3,
            "observed_signature_cluster_size": 3,
            "mirror_only_detected": False,
            "comfort_only_surface_detected": False,
            "forbidden_surface_classes_present": ["comfort_only"],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
        "p3-structure_question-003": {
            "section_role_sequence": ["reception"],
            "opening_shape_family": "question_only_opening",
            "closing_shape_family": "question_only_closing",
            "observed_temperature_profile": "generic_reception_flattened",
            "observed_anchor_roles": [],
            "observation_anchor_count": 0,
            "reception_anchor_count": 0,
            "generic_empathy_marker_count": 0,
            "question_count": 1,
            "question_position": "primary",
            "same_closing_family_repetition_count": 1,
            "same_section_role_sequence_repetition_count": 1,
            "observed_signature_cluster_size": 1,
            "mirror_only_detected": False,
            "comfort_only_surface_detected": False,
            "forbidden_surface_classes_present": [],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
        "p3-self_denial-001": {
            "section_role_sequence": ["observation", "reception"],
            "opening_shape_family": "self_denial_state_not_fact_opening",
            "closing_shape_family": "careful_support_closing",
            "observed_temperature_profile": "careful_support_without_identity_confirmation",
            "observed_anchor_roles": [
                "self_denial_phrase_as_state_not_fact",
                "no_identity_claim_marker",
                "emlis_reception_anchor",
            ],
            "observation_anchor_count": 2,
            "reception_anchor_count": 1,
            "generic_empathy_marker_count": 0,
            "question_count": 0,
            "question_position": "none",
            "same_closing_family_repetition_count": 1,
            "same_section_role_sequence_repetition_count": 1,
            "observed_signature_cluster_size": 1,
            "mirror_only_detected": False,
            "comfort_only_surface_detected": False,
            "forbidden_surface_classes_present": [],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
        "p3-low_information_short-001": {
            "section_role_sequence": ["observation", "reception"],
            "opening_shape_family": "visible_scope_opening",
            "closing_shape_family": "gentle_reception_closing",
            "observed_temperature_profile": "limited_scope_reception",
            "observed_anchor_roles": [
                "visible_scope_marker",
                "unknown_scope_marker",
                "emlis_reception_anchor",
            ],
            "observation_anchor_count": 2,
            "reception_anchor_count": 1,
            "generic_empathy_marker_count": 0,
            "question_count": 1,
            "question_position": "after_reception_optional",
            "same_closing_family_repetition_count": 1,
            "same_section_role_sequence_repetition_count": 1,
            "observed_signature_cluster_size": 1,
            "mirror_only_detected": False,
            "comfort_only_surface_detected": False,
            "forbidden_surface_classes_present": [],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
        "p3-structure_question-005": {
            "section_role_sequence": ["observation", "reception"],
            "opening_shape_family": "limited_visible_scope_opening",
            "closing_shape_family": "limited_grounding_reception_closing",
            "observed_temperature_profile": "limited_scope_reception",
            "observed_anchor_roles": [
                "visible_scope_marker",
                "limited_grounding_marker",
                "soft_inference_marker",
                "emlis_reception_anchor",
            ],
            "observation_anchor_count": 3,
            "reception_anchor_count": 1,
            "generic_empathy_marker_count": 0,
            "question_count": 0,
            "question_position": "none",
            "same_closing_family_repetition_count": 1,
            "same_section_role_sequence_repetition_count": 1,
            "observed_signature_cluster_size": 1,
            "mirror_only_detected": False,
            "comfort_only_surface_detected": False,
            "forbidden_surface_classes_present": [],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "gate_relaxed": False,
        },
    }
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        observations, source="p4_5.fixture_surface_signature_observations"
    )
    return observations


def build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    family_tuning_policy_payload: Mapping[str, Any] | None = None,
    surface_signature_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    target_selection = target_case_selection_payload or build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id=run_id or "p4_5_source_p4_1_target_selection"
    )
    material_audit = material_audit_payload or build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        target_case_selection_payload=target_selection,
        run_id=run_id or "p4_5_source_p4_2_material_audit",
    )
    family_policy = family_tuning_policy_payload or build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
        target_case_selection_payload=target_selection,
        material_audit_payload=material_audit,
        run_id=run_id or "p4_5_source_p4_4_family_policy",
    )
    observations = surface_signature_observations_by_case_ref_id or build_product_readfeel_p4_surface_signature_observations_20260610()
    audit = build_product_readfeel_p4_surface_signature_audit_20260610(
        target_case_selection_payload=target_selection,
        material_audit_payload=material_audit,
        family_tuning_policy_payload=family_policy,
        surface_signature_observations_by_case_ref_id=observations,
        run_id=run_id or "p4_5_surface_signature_audit_fixture",
    )
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(audit)
    return audit


def build_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    family_tuning_policy_payload: Mapping[str, Any] | None = None,
    surface_signature_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    audit = build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610(
        target_case_selection_payload=target_case_selection_payload,
        material_audit_payload=material_audit_payload,
        family_tuning_policy_payload=family_tuning_policy_payload,
        surface_signature_observations_by_case_ref_id=surface_signature_observations_by_case_ref_id,
        run_id=run_id,
    )
    return build_product_readfeel_p4_surface_signature_audit_public_summary_20260610(audit)


def dump_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    family_tuning_policy_payload: Mapping[str, Any] | None = None,
    surface_signature_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610(
        target_case_selection_payload=target_case_selection_payload,
        material_audit_payload=material_audit_payload,
        family_tuning_policy_payload=family_tuning_policy_payload,
        surface_signature_observations_by_case_ref_id=surface_signature_observations_by_case_ref_id,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610",
    "assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610",
    "build_product_readfeel_p4_surface_signature_audit_from_p4_1_p4_2_p4_4_20260610",
    "build_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610",
    "build_product_readfeel_p4_surface_signature_observations_20260610",
    "dump_product_readfeel_p4_surface_signature_audit_summary_from_p4_1_p4_2_p4_4_20260610",
]
