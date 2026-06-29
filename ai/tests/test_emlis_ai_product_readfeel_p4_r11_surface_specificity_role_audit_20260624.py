# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
import emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit as r11_r6r7
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
    build_product_readfeel_baseline_public_safe_index_20260609,
)

FORBIDDEN_BODY_TOKENS = (
    '"raw_input":',
    '"raw_text":',
    '"current_input":',
    '"memo":',
    '"memo_text":',
    '"memo_action":',
    '"comment_text":',
    '"comment_text_body":',
    '"candidate_body":',
    '"surface_text":',
    '"display_text":',
    '"visible_text":',
    '"reviewer_note":',
    '"question_text":',
    '"draft_question_text":',
    '"stdout":',
    '"stderr":',
    '"traceback_body":',
)
FORBIDDEN_PROMOTION_TOKENS = (
    '"p8_start_allowed": true',
    '"release_allowed": true',
    '"runtime_changed_here": true',
    '"question_implementation_started_here": true',
    '"actual_human_review_run_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_audit_rows_created_here": true',
    '"json_schema_file_materialized": true',
    '"local_visible_surface_retained_here": true',
    '"local_comment_text_retained_here": true',
    '"detector_fragment_retained_here": true',
    '"exact_sentence_match_required": true',
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def _assert_body_free(value: object) -> None:
    dumped = _dump(value)
    for token in FORBIDDEN_BODY_TOKENS:
        assert token not in dumped
    for token in FORBIDDEN_PROMOTION_TOKENS:
        assert token not in dumped


@lru_cache(maxsize=1)
def _cached_sources() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    return (
        build_product_readfeel_baseline_public_safe_index_20260609(),
        build_product_readfeel_baseline_cases_20260609(),
    )


def _baseline() -> list[dict[str, object]]:
    return deepcopy(_cached_sources()[0])


def _local_cases() -> list[dict[str, object]]:
    return deepcopy(_cached_sources()[1])


def _surface_path_audit() -> dict[str, object]:
    baseline = _baseline()
    scope = r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r6_test_scope",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_r6_test_selection",
    )
    material = r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=selection,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r6_test_material",
    )
    return r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
        material_route_audit_payload=material,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_r6_test_surface_path",
    )


def _passing_probe_for_row(row: dict[str, object]) -> str:
    return " ".join(str(role) for role in row.get("required_surface_role_ids") or ())


def _probe_rows(
    surface_path_payload: dict[str, object],
    *,
    overrides: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    overrides = overrides or {}
    probes: list[dict[str, str]] = []
    for row in surface_path_payload["audit_rows"]:
        assert isinstance(row, dict)
        case_ref = str(row["case_ref_id"])
        probes.append(
            {
                "case_ref_id": case_ref,
                "local_visible_surface": overrides.get(case_ref, _passing_probe_for_row(row)),
            }
        )
    return probes


def _first_case_ref(surface_path_payload: dict[str, object], residual_family_id: str) -> str:
    for row in surface_path_payload["audit_rows"]:
        assert isinstance(row, dict)
        if row.get("residual_family_id") == residual_family_id:
            return str(row["case_ref_id"])
    raise AssertionError(f"missing residual family in R11 test fixture: {residual_family_id}")


def test_r11_6_surface_specificity_role_audit_returns_only_role_and_signature_ids() -> None:
    surface_path = _surface_path_audit()
    daily_ref = _first_case_ref(surface_path, r11.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY)
    probes = _probe_rows(
        surface_path,
        overrides={
            daily_ref: (
                "positive_event_or_small_change_visible "
                "reception_warmth_present "
                "generic_praise_only"
            )
        },
    )

    payload = r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
        surface_path_audit_payload=surface_path,
        local_surface_probes=probes,
        run_id="p4_r11_r6_test_specificity",
    )
    summary = payload["summary"]
    rows = payload["audit_rows"]

    assert payload["schema_version"] == r11_r6r7.PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624
    assert payload["source_step"] == r11.P4_R11_R6_STEP_REF_20260624
    assert tuple(payload["implemented_steps"]) == r11_r6r7.P4_R11_R6_IMPLEMENTED_STEPS_20260624
    assert payload["next_implementation_step"] == r11.P4_R11_R7_STEP_REF_20260624
    assert payload["surface_specificity_role_audit_performed_here"] is True
    assert payload["verdict_classification_performed_here"] is False
    assert payload["actual_audit_rows_created_here"] is False

    assert summary["audited_row_count"] == r11.P4_R11_TARGET_ROW_COUNT_20260624
    assert summary["surface_probe_unavailable_count"] == 0
    assert summary["specificity_gap_count"] >= 1
    assert summary["generic_surface_signature_counts"]["generic_praise_only"] == 1
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False

    daily_row = next(row for row in rows if row["case_ref_id"] == daily_ref)
    assert daily_row["surface_specificity_role_audit_status"] == "audited_r11_6"
    assert daily_row["verdict_status"] == "not_run_r11_7"
    assert "generic_praise_only" in daily_row["generic_surface_signature_ids"]
    assert "no_generic_praise_only" in daily_row["missing_surface_role_ids"]
    assert daily_row["local_visible_surface_retained_here"] is False
    assert daily_row["detector_fragment_retained_here"] is False
    assert daily_row["exact_sentence_match_required"] is False

    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload)
    _assert_body_free(payload)


def test_r11_6_normalizer_does_not_return_local_probe_body_or_exact_fragments() -> None:
    normalized = r11_r6r7.normalize_local_surface_probe_to_p4_r11_observation_ids_20260624(
        local_visible_surface=(
            "future_direction_visible "
            "recovered_energy_or_transition_visible "
            "category_emotion_action_generic"
        ),
        residual_family_id=r11.SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION,
        residual_focus_slice_ids=("future_direction", "recovered_energy"),
    )

    assert "future_direction_visible" in normalized["observed_surface_role_ids"]
    assert "category_emotion_action_generic" in normalized["generic_surface_signature_ids"]
    assert normalized["local_visible_surface_retained_here"] is False
    assert normalized["detector_fragment_retained_here"] is False
    assert normalized["exact_sentence_match_required"] is False
    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(normalized)
    _assert_body_free(normalized)


def test_r11_6_rejects_payload_that_skips_r11_5_surface_path_audit() -> None:
    surface_path = _surface_path_audit()
    broken = deepcopy(surface_path)
    broken["audit_rows"][0]["surface_path_audit_performed_here"] = False

    with pytest.raises(ValueError, match="requires R11-5 surface path audit"):
        r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
            surface_path_audit_payload=broken,
            local_surface_probes=_probe_rows(surface_path),
            run_id="p4_r11_r6_test_reject_skip_r11_5",
        )
