# -*- coding: utf-8 -*-
from __future__ import annotations

"""P2 tests for GateRecoveryPublicBoundaryDecision.

These tests cover the meta-only public-boundary decision. Runtime adoption inside
recover_emlis_gate_failure remains P3.
"""

from dataclasses import dataclass, field
from typing import Any

from emlis_ai_gate_recovery_public_boundary import (
    DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED,
    assert_gate_recovery_public_boundary_decision,
    decide_gate_recovery_public_boundary,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_RECOVERY_SURFACE_SOURCE_LINEAGE_MISSING,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_NONE,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)


@dataclass
class _Candidate:
    composer_model: str = ""
    generation_method: str = ""
    composer_meta: dict[str, Any] = field(default_factory=dict)


def _assert_meta_only(decision: dict[str, Any]) -> None:
    assert decision["schema_version"] == GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION
    assert decision["contract_flags"] == {
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    assert "comment_text" not in decision
    assert "raw_input" not in decision
    assert_gate_recovery_public_boundary_decision(decision)


def test_p2_blocks_phase20_5_material_surface_model_meta_only() -> None:
    decision = decide_gate_recovery_public_boundary(
        candidate=_Candidate(
            composer_model=GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
            generation_method=GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
            composer_meta={
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
                "surface_generation_method": "material_bound_generic_surface",
            },
        ),
        composer_resolution={"rejection_reasons": [DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED]},
    )

    assert decision["public_display_allowed"] is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in decision["blockers"]
    assert BLOCKER_RECOVERY_SURFACE_SOURCE_LINEAGE_MISSING in decision["blockers"]
    assert BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION in decision["blockers"]
    assert decision["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    assert decision["public_surface_role"] == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    _assert_meta_only(decision)


def test_p2_blocks_post_final_material_surface_model_and_context() -> None:
    decision = decide_gate_recovery_public_boundary(
        candidate=_Candidate(
            composer_model=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
            generation_method=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
            composer_meta={
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
            },
        ),
        recovery_context="post_final_pre_return_gate",
    )

    assert decision["public_display_allowed"] is False
    assert decision["recovery_context"] == "post_final_pre_return_gate"
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in decision["blockers"]
    _assert_meta_only(decision)


def test_p2_blocks_diagnostic_role_even_when_template_meta_was_false_negative() -> None:
    decision = decide_gate_recovery_public_boundary(
        candidate=_Candidate(
            composer_meta={
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
                "surface_quality_signature": {
                    "surface_template_major": False,
                    "template_major": False,
                },
            }
        )
    )

    assert decision["public_display_allowed"] is False
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    _assert_meta_only(decision)


def test_p2_blocks_material_bound_surface_without_public_rebuild_lineage() -> None:
    decision = decide_gate_recovery_public_boundary(
        candidate=_Candidate(
            composer_meta={
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NONE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "surface_generation_method": "material_bound_generic_surface",
            }
        )
    )

    assert decision["public_display_allowed"] is False
    assert BLOCKER_RECOVERY_SURFACE_SOURCE_LINEAGE_MISSING in decision["blockers"]
    _assert_meta_only(decision)


def test_p2_allows_allowed_public_source_with_public_observation_role() -> None:
    decision = decide_gate_recovery_public_boundary(
        candidate=_Candidate(
            composer_model="complete_initial_composer_v1",
            generation_method="complete_initial_composer",
            composer_meta={
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "candidate_lineage": {
                    "original_candidate_present": True,
                    "original_candidate_source": "complete_initial_composer",
                    "recovery_plan_used": False,
                    "diagnostic_surface_used": False,
                    "public_candidate_rebuilt_after_recovery": False,
                },
            },
        )
    )

    assert decision["public_display_allowed"] is True
    assert decision["blockers"] == []
    assert decision["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER
    _assert_meta_only(decision)


def test_p2_allows_bounded_repaired_original_when_rebuilt_lineage_exists() -> None:
    decision = decide_gate_recovery_public_boundary(
        candidate=_Candidate(
            composer_model="bounded_repaired_original_candidate_v1",
            generation_method="bounded_repair_after_gate_recovery",
            composer_meta={
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "surface_generation_method": "material_bound_generic_surface",
                "candidate_lineage": {
                    "original_candidate_present": True,
                    "original_candidate_source": "limited_composer",
                    "recovery_plan_used": True,
                    "diagnostic_surface_used": True,
                    "public_candidate_rebuilt_after_recovery": True,
                },
            },
        )
    )

    assert decision["public_display_allowed"] is True
    assert decision["blockers"] == []
    assert decision["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    _assert_meta_only(decision)
