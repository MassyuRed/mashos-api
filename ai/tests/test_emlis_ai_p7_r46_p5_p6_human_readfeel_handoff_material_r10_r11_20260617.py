# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_HOLD_REF,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P6_LIMITED_HUMAN_READFEEL_HOLD_REF,
    P6_LIMITED_READFEEL_RATING_AXES,
    P6_LIMITED_READFEEL_REVIEW_FAMILIES,
    P6_NO_CONNECT_FAMILIES,
    P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION,
    P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION,
    P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION,
    assert_p5_human_blind_qa_handoff_material_contract,
    assert_p5_p6_human_readfeel_handoff_summary_contract,
    assert_p6_limited_human_readfeel_handoff_material_contract,
    build_p5_human_blind_qa_handoff_material,
    build_p5_p6_human_readfeel_handoff_summary,
    build_p6_limited_human_readfeel_handoff_material,
)

SECRET_INPUT = "R10/R11 secret raw input must never enter handoff material"
SECRET_SURFACE = "R10/R11 secret returned surface must never enter handoff material"
SECRET_REVIEWER_NOTE = "R10/R11 reviewer note must never enter handoff material"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_r10_p5_human_blind_qa_handoff_is_body_free_release_closed_and_keeps_hold001() -> None:
    material = build_p5_human_blind_qa_handoff_material(
        [
            {
                "case_id": "p5_history_case_001",
                "family": "history_line_eligible_input",
                "subscription_tier": "plus",
                "source_row_ref": "scorecard_row_001",
                "eligible": True,
                "visible_applied": True,
                "runtime_evaluated": True,
            }
        ]
    )
    assert_p5_human_blind_qa_handoff_material_contract(material)

    assert material["schema_version"] == P7_R46_P5_HUMAN_BLIND_QA_HANDOFF_SCHEMA_VERSION
    assert material["review_scope"] == "local_human_review_only_not_public_meta"
    assert material["p5_human_blind_qa_ready"] is True
    assert material["p5_human_blind_qa_confirmed"] is False
    assert material["human_review_completed"] is False
    assert material["release_allowed"] is False
    assert material["p7_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["body_free"] is True
    assert material["families"] == list(P5_HUMAN_BLIND_QA_FAMILIES)
    assert material["rating_axes"] == list(P5_HUMAN_BLIND_QA_RATING_AXES)
    assert P5_HUMAN_BLIND_QA_HOLD_REF in material["unresolved_hold_refs"]
    assert material["review_body_packet_boundary"]["local_body_packet_required"] is True
    assert material["review_body_packet_boundary"]["local_body_packet_materialized_here"] is False
    assert material["review_body_packet_boundary"]["local_body_packet_release_material"] is False
    assert material["case_refs"][0]["body_free"] is True

    dumped = _dumped(material)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER_NOTE not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r11_p6_limited_human_readfeel_handoff_keeps_target_and_no_connect_families_closed() -> None:
    material = build_p6_limited_human_readfeel_handoff_material(
        [
            {
                "case_id": "p6_structure_case_001",
                "family": "structure_question",
                "subscription_tier": "premium",
                "source_row_ref": "scorecard_row_006",
                "eligible": True,
                "visible_applied": True,
                "runtime_evaluated": True,
            },
            {
                "case_id": "p6_daily_no_connect_001",
                "family": "daily_positive",
                "subscription_tier": "plus",
                "source_row_ref": "scorecard_row_007",
                "eligible": False,
                "visible_applied": False,
                "runtime_evaluated": True,
            },
        ]
    )
    assert_p6_limited_human_readfeel_handoff_material_contract(material)

    assert material["schema_version"] == P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION
    assert material["review_families"] == list(P6_LIMITED_READFEEL_REVIEW_FAMILIES)
    assert material["no_connect_families"] == list(P6_NO_CONNECT_FAMILIES)
    assert material["rating_axes"] == list(P6_LIMITED_READFEEL_RATING_AXES)
    assert material["p6_limited_human_readfeel_review_ready"] is True
    assert material["p6_human_readfeel_review_confirmed"] is False
    assert material["visible_expansion_allowed"] is False
    assert material["visible_expansion_requires_future_design"] is True
    assert material["history_used_as_fact_allowed"] is False
    assert material["p5_history_line_substitution_allowed"] is False
    assert P6_LIMITED_HUMAN_READFEEL_HOLD_REF in material["unresolved_hold_refs"]
    assert material["release_allowed"] is False
    assert material["body_free"] is True

    dumped = _dumped(material)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER_NOTE not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"body":' not in dumped
    assert '"text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r10_r11_combined_summary_preserves_p7_phase_and_does_not_claim_human_review_done() -> None:
    summary = build_p5_p6_human_readfeel_handoff_summary()
    assert_p5_p6_human_readfeel_handoff_summary_contract(summary)

    assert summary["schema_version"] == P7_R46_P5_P6_HUMAN_READFEEL_HANDOFF_SUMMARY_SCHEMA_VERSION
    assert summary["current_phase"] == "P7"
    assert summary["p5_human_blind_qa_ready"] is True
    assert summary["p5_human_blind_qa_confirmed"] is False
    assert summary["p6_limited_human_readfeel_review_ready"] is True
    assert summary["p6_human_readfeel_review_confirmed"] is False
    assert summary["human_review_not_run"] is True
    assert summary["actual_review_bodies_materialized_here"] is False
    assert {P5_HUMAN_BLIND_QA_HOLD_REF, P6_LIMITED_HUMAN_READFEEL_HOLD_REF}.issubset(
        set(summary["unresolved_hold_refs"])
    )
    assert summary["release_allowed"] is False
    assert summary["p7_complete"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["body_free"] is True


@pytest.mark.parametrize(
    "builder",
    [build_p5_human_blind_qa_handoff_material, build_p6_limited_human_readfeel_handoff_material],
)
def test_r10_r11_handoff_builders_reject_raw_body_case_refs(builder) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        builder(
            [
                {
                    "case_id": "unsafe_case",
                    "family": "structure_question",
                    "raw_input": SECRET_INPUT,
                    "comment_text": SECRET_SURFACE,
                    "reviewer_free_text": SECRET_REVIEWER_NOTE,
                }
            ]
        )


def test_r10_r11_contracts_reject_release_promotion_and_p6_visible_expansion() -> None:
    p5 = build_p5_human_blind_qa_handoff_material()
    p5["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p5_human_blind_qa_handoff_material_contract(p5)

    p6 = build_p6_limited_human_readfeel_handoff_material()
    p6["visible_expansion_allowed"] = True
    with pytest.raises(ValueError):
        assert_p6_limited_human_readfeel_handoff_material_contract(p6)

    summary = build_p5_p6_human_readfeel_handoff_summary()
    summary["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        assert_p5_p6_human_readfeel_handoff_summary_contract(summary)
