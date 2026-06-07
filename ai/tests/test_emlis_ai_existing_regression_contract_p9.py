# -*- coding: utf-8 -*-
from __future__ import annotations

"""P9 existing regression / public contract checks for reception-required surfaces.

P9 does not add a new public API shape.  It freezes that the P0-P8
limited_grounding / true low_information reception-required work still respects
existing RN/API/DB/Gate boundaries while product validation can detect the new
surface shape without copying raw input or comment bodies into public meta.
"""

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_product_surface_validation import (
    PRODUCT_SURFACE_VALID,
    PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY,
    assert_product_surface_validation_summary,
    build_product_surface_validation_summary,
    product_surface_validation_public_summary,
)
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_public_surface_requirement import (
    LABELLED_TWO_STAGE_OBSERVATION_MARKER,
    LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    public_surface_requirement_public_summary,
    resolve_public_surface_requirement,
)
from emlis_ai_response_contract import (
    EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY,
    build_emlis_internal_response_contract,
)

_SECRET_RAW_INPUT = "P9_PUBLIC_META_RAW_INPUT_MUST_NOT_LEAK"
_SECRET_COMMENT = "P9_PUBLIC_META_COMMENT_BODY_MUST_NOT_LEAK"

_LIMITED_COMMENT = (
    "見えたこと：\n"
    "今見えているのは、気力が戻ってきた今を大切にしようとしている動きです。\n\n"
    "Emlisから：\n"
    "まだ詳しい出来事までは断定せず、その言葉を置いたことをEmlisは受け取りました。"
)
_LOW_INFORMATION_COMMENT = (
    "見えたこと：\n"
    "今は、詳しい出来事まではまだ見えていません。\n\n"
    "Emlisから：\n"
    "整理できていない状態でも、そのまま置いたことをEmlisは受け取りました。"
    "詳しくできそうなら、あとで一つだけ足してみませんか。"
)


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_secret_text(value: Any) -> None:
    dumped = _dump(value)
    assert _SECRET_RAW_INPUT not in dumped
    assert _SECRET_COMMENT not in dumped


def _assert_false_flags(value: Mapping[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        assert value.get(key) is False, key


@pytest.mark.parametrize(
    ("material_quality", "expected_family", "expected_two_stage", "expected_low_info_allowed", "expected_source"),
    (
        (
            "limited_grounding",
            SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            True,
            False,
            "limited_grounding_reception_required",
        ),
        (
            "low_information",
            SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
            False,
            True,
            "low_information_reception_required",
        ),
    ),
)
def test_p9_surface_requirement_keeps_reception_shape_without_contract_or_gate_relaxation(
    material_quality: str,
    expected_family: str,
    expected_two_stage: bool,
    expected_low_info_allowed: bool,
    expected_source: str,
) -> None:
    requirement = resolve_public_surface_requirement(
        current_input={
            "memo": _SECRET_RAW_INPUT,
            "memo_action": "",
            "emotions": ["平穏"],
            "category": ["生活"],
        },
        material_route={"material_quality": material_quality},
    )

    assert requirement["surface_requirement_family"] == expected_family
    assert requirement["material_quality_family"] == material_quality
    assert requirement["two_stage_required"] is expected_two_stage
    assert requirement["low_information_allowed"] is expected_low_info_allowed
    assert expected_source in requirement["decision_sources"]

    shape = requirement["required_comment_text_shape"]
    assert shape["starts_with"] == LABELLED_TWO_STAGE_OBSERVATION_MARKER
    assert shape["contains_boundary"] == LABELLED_TWO_STAGE_RECEPTION_BOUNDARY
    assert shape["labels_required"] is True
    assert shape["observation_section_required"] is True
    assert shape["reception_section_required"] is True
    assert shape["comment_text_body_included"] is False

    _assert_false_flags(
        requirement["public_contract"],
        (
            "public_response_key_added",
            "rn_visible_contract_changed",
            "response_shape_changed",
            "api_route_changed",
            "db_physical_name_changed",
        ),
    )
    _assert_false_flags(
        requirement["gate_policy"],
        (
            "display_gate_relaxed",
            "runtime_surface_gate_relaxed",
            "visible_surface_gate_relaxed",
            "grounding_gate_relaxed",
            "template_gate_relaxed",
            "safety_gate_relaxed",
        ),
    )
    _assert_no_secret_text(requirement)

    public_summary = public_surface_requirement_public_summary(requirement)
    _assert_no_secret_text(public_summary)
    assert public_summary["body_free"] is True
    assert public_summary["raw_input_included"] is False
    assert public_summary["comment_text_body_included"] is False


@pytest.mark.parametrize(
    ("material_quality", "candidate_source_kind", "comment_text", "expected_family", "expected_low_info"),
    (
        (
            "limited_grounding",
            "labelled_two_stage_surface_recomposition_candidate",
            _LIMITED_COMMENT,
            SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            False,
        ),
        (
            "low_information",
            "low_information_observation_composer",
            _LOW_INFORMATION_COMMENT,
            SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
            True,
        ),
    ),
)
def test_p9_product_surface_validation_accepts_reception_required_shape_and_keeps_body_free_meta(
    material_quality: str,
    candidate_source_kind: str,
    comment_text: str,
    expected_family: str,
    expected_low_info: bool,
) -> None:
    requirement = resolve_public_surface_requirement(
        current_input={"memo": _SECRET_RAW_INPUT, "emotions": ["平穏"], "category": ["生活"]},
        material_route={"material_quality": material_quality},
    )
    summary = build_product_surface_validation_summary(
        input_feedback_included=True,
        comment_text=comment_text,
        emlis_ai_public_meta={"observation_status": "passed"},
        surface_requirement=requirement,
        candidate_generation_summary={
            "candidate_source_kind": candidate_source_kind,
            "composer_source": "ai_generated",
            "candidate_status": "generated",
            "candidate_comment_text": _SECRET_COMMENT,
            "current_input": {"memo": _SECRET_RAW_INPUT},
        },
    )

    assert_product_surface_validation_summary(summary)
    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_VALID
    assert summary["surface_requirement_family"] == expected_family
    assert summary["low_information_surface_used"] is expected_low_info
    assert summary["question_dominance_guard"]["checked"] is True
    assert summary["question_dominance_guard"]["passed"] is True
    assert summary["question_dominance_guard"]["reception_section_present"] is True
    assert summary["question_dominance_guard"]["question_before_reception"] is False
    assert summary["body_free"] is True
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    _assert_no_secret_text(summary)

    public_summary = product_surface_validation_public_summary(summary)
    assert public_summary["product_surface_valid"] is True
    assert public_summary["question_dominance_guard"]["passed"] is True
    assert public_summary["body_free"] is True
    assert public_summary["raw_input_included"] is False
    assert public_summary["comment_text_body_included"] is False
    _assert_no_secret_text(public_summary)


def test_p9_public_feedback_meta_can_expose_product_validation_without_comment_or_raw_input_leakage() -> None:
    requirement = resolve_public_surface_requirement(
        current_input={"memo": _SECRET_RAW_INPUT, "emotions": ["平穏"], "category": ["生活"]},
        material_route={"material_quality": "limited_grounding"},
    )
    product_summary = build_product_surface_validation_summary(
        input_feedback_included=True,
        comment_text=_LIMITED_COMMENT,
        emlis_ai_public_meta={"observation_status": "passed"},
        surface_requirement=requirement,
        candidate_generation_summary={
            "candidate_source_kind": "labelled_two_stage_surface_recomposition_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
            "candidate_comment_text": _SECRET_COMMENT,
            "current_input": {"memo": _SECRET_RAW_INPUT},
        },
    )
    internal_contract = build_emlis_internal_response_contract(
        "limited_grounding_observation",
        reason="p9_contract_limited_grounding_public_feedback",
    )

    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "rejected",
            "rejection_reasons": ["legacy_display_gate_failed_before_p9_recovery"],
            EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: internal_contract,
            PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY: product_summary,
            "candidate_comment_text": _SECRET_COMMENT,
            "current_input": {"memo": _SECRET_RAW_INPUT},
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback(_LIMITED_COMMENT, public_meta) is True
    assert PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY in public_meta
    assert public_meta[PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY]["product_surface_valid"] is True
    assert public_meta[PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY]["question_dominance_guard"]["passed"] is True
    assert public_meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False
    assert "internal_response_contract" not in public_meta
    _assert_no_secret_text(public_meta)


@pytest.mark.parametrize(
    ("response_kind", "expected_status"),
    (
        ("safety_blocked_emergency", "safety_blocked"),
        ("infrastructure_error", "unavailable"),
    ),
)
def test_p9_safety_and_infra_contracts_are_not_faked_as_public_observations(
    response_kind: str,
    expected_status: str,
) -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: build_emlis_internal_response_contract(
                response_kind,
                reason=f"p9_contract_{response_kind}",
            ),
            "comment_text": _SECRET_COMMENT,
            "current_input": {"memo": _SECRET_RAW_INPUT},
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["observation_status"] == expected_status
    assert should_include_public_input_feedback(_LIMITED_COMMENT, public_meta) is False
    _assert_no_secret_text(public_meta)
