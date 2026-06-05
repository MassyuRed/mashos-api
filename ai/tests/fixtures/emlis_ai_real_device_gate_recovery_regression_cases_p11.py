# -*- coding: utf-8 -*-
from __future__ import annotations

"""P11 real-device regression fixture handling for Gate Recovery public leaks.

The F/E/G screenshots are kept as local regression fixture *metadata* only.
They are not runtime routes, they do not lock exact public comment_text, and
fixture strings must not be used as production branching conditions.  The
fixture exists to assert forbidden public fragments and source lineage: a
Gate Recovery material surface must never be the final public candidate, while
allowed public candidates are judged by their source kind and gates rather than
by exact body equality.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
)

P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_VERSION: Final = (
    "cocolon.emlis.real_device.gate_recovery_regression_fixture.v1"
)
P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_SOURCE: Final = (
    "real_device_feg_gate_recovery_public_leak_2026_06_05"
)
P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION: Final = "p11_20260605"

P11_FORBIDDEN_PUBLIC_FRAGMENTS: Final[tuple[str, ...]] = (
    "今回の入力では",
    "原因や結論までは決めず",
    "誰かを良い悪いで決めず",
)

P11_FORBIDDEN_SURFACE_CLASSES: Final[tuple[str, ...]] = (
    "gate_recovery_material_surface_public_fallback",
    "diagnostic_recovery_surface_to_comment_text",
    "internal_policy_sentence_public_display",
    "material_slot_echo_only",
    "category_emotion_slot_label_listing",
    "case_specific_runtime_branch",
    "exact_comment_text_lock",
)

P11_ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS: Final[tuple[str, ...]] = tuple(
    sorted(ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS)
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
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_text",
        "currentText",
        "emotion_details",
        "comment_text",
        "commentText",
        "expected_comment_text",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "realized_text",
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
    "expected_comment_text_locked",
    "exact_comment_text_locked",
    "exact_comment_text_required",
    "case_specific_runtime_branch",
    "case_specific_runtime_condition_allowed",
    "runtime_branching_uses_fixture_strings",
    "fixture_text_used_for_runtime_branching",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "public_status_extended",
    "observation_status_enum_extended",
    "response_shape_changed",
    "public_response_key_change",
    "public_response_key_added",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "product_gate_ready",
    "public_release_applied",
    "product_quality_released",
    "external_ai_used",
    "local_llm_used",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _as_tuple(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in values if str(item).strip())


@dataclass(frozen=True)
class RealDeviceGateRecoveryRegressionFixtureP11:
    fixture_id: str
    real_device_case_label: str
    family: str
    observed_surface_model: str
    observed_generation_method: str
    observed_recovery_context: str
    expected_blockers_when_leaked: tuple[str, ...]
    expected_allowed_public_candidate_source_kinds: tuple[str, ...] = P11_ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
    forbidden_public_fragments: tuple[str, ...] = P11_FORBIDDEN_PUBLIC_FRAGMENTS
    forbidden_surface_classes: tuple[str, ...] = P11_FORBIDDEN_SURFACE_CLASSES
    source: str = P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_SOURCE
    source_date: str = "2026-06-05"
    source_revision: str = P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION
    schema_version: str = P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_VERSION
    exact_comment_text_required: bool = False
    exact_comment_text_locked: bool = False
    exact_runtime_condition_allowed: bool = False
    case_specific_runtime_branch: bool = False
    case_specific_runtime_condition_allowed: bool = False
    runtime_branching_uses_fixture_strings: bool = False
    fixture_text_used_for_runtime_branching: bool = False
    raw_input_included: bool = False
    comment_text_body_included: bool = False
    candidate_body_included: bool = False
    public_release_applied: bool = False
    product_gate_ready: bool = False

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "fixture_id": self.fixture_id,
            "source": self.source,
            "source_date": self.source_date,
            "source_revision": self.source_revision,
            "real_device_case_label": self.real_device_case_label,
            "family": self.family,
            "observed_surface_model": self.observed_surface_model,
            "observed_generation_method": self.observed_generation_method,
            "observed_recovery_context": self.observed_recovery_context,
            "expected_allowed_public_candidate_source_kinds": list(
                self.expected_allowed_public_candidate_source_kinds
            ),
            "expected_blockers_when_leaked": list(self.expected_blockers_when_leaked),
            "forbidden_public_fragments": list(self.forbidden_public_fragments),
            "forbidden_surface_classes": list(self.forbidden_surface_classes),
            "exact_comment_text_required": self.exact_comment_text_required,
            "exact_comment_text_locked": self.exact_comment_text_locked,
            "exact_runtime_condition_allowed": self.exact_runtime_condition_allowed,
            "case_specific_runtime_branch": self.case_specific_runtime_branch,
            "case_specific_runtime_condition_allowed": self.case_specific_runtime_condition_allowed,
            "runtime_branching_uses_fixture_strings": self.runtime_branching_uses_fixture_strings,
            "fixture_text_used_for_runtime_branching": self.fixture_text_used_for_runtime_branching,
            "raw_input_included": self.raw_input_included,
            "comment_text_body_included": self.comment_text_body_included,
            "candidate_body_included": self.candidate_body_included,
            "public_release_applied": self.public_release_applied,
            "product_gate_ready": self.product_gate_ready,
        }

    def as_product_quality_input_case(self) -> dict[str, Any]:
        return {
            "case_id": self.fixture_id,
            "source_type": "regression_fixture",
            "source_revision": self.source_revision,
            "family": self.family,
            # Transient renderer metadata only.  This is not raw user input and
            # ProductQualityMeasurementRun does not serialize current_input.
            "current_input": {
                "id": self.fixture_id,
                "p11_real_device_case_label": self.real_device_case_label,
                "p11_observed_surface_model": self.observed_surface_model,
                "p11_observed_generation_method": self.observed_generation_method,
            },
        }


P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES: Final[
    tuple[RealDeviceGateRecoveryRegressionFixtureP11, ...]
] = (
    RealDeviceGateRecoveryRegressionFixtureP11(
        fixture_id="p11_real_device_f_gate_recovery_public_leak_regression",
        real_device_case_label="F",
        family="relationship_boundary",
        observed_surface_model=GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        observed_generation_method=GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
        observed_recovery_context="pre_public_display_gate",
        expected_blockers_when_leaked=(
            BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
            BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
        ),
    ),
    RealDeviceGateRecoveryRegressionFixtureP11(
        fixture_id="p11_real_device_e_gate_recovery_public_leak_regression",
        real_device_case_label="E",
        family="daily_positive",
        observed_surface_model=GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        observed_generation_method=GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
        observed_recovery_context="pre_public_display_gate",
        expected_blockers_when_leaked=(
            BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
            BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
        ),
    ),
    RealDeviceGateRecoveryRegressionFixtureP11(
        fixture_id="p11_real_device_g_post_final_gate_recovery_public_leak_regression",
        real_device_case_label="G",
        family="mixed_emotion",
        observed_surface_model=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        observed_generation_method=POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
        observed_recovery_context="post_final_pre_return_gate",
        expected_blockers_when_leaked=(
            BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
            BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
        ),
    ),
)


def build_p11_real_device_gate_recovery_regression_fixtures() -> list[dict[str, Any]]:
    return [fixture.as_meta() for fixture in P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES]


def build_p11_real_device_product_quality_input_cases() -> list[dict[str, Any]]:
    return [fixture.as_product_quality_input_case() for fixture in P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES]


def get_p11_fixture_by_id(fixture_id: str) -> RealDeviceGateRecoveryRegressionFixtureP11:
    target = _clean(fixture_id)
    for fixture in P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES:
        if fixture.fixture_id == target:
            return fixture
    raise KeyError(f"unknown P11 real-device fixture id: {fixture_id}")


def assert_p11_real_device_gate_recovery_fixture_meta_only(value: Any) -> None:
    if isinstance(value, Mapping):
        overlap = set(value.keys()) & _TEXT_PAYLOAD_KEYS
        if overlap:
            raise ValueError(f"P11 fixture contains forbidden text payload keys: {sorted(overlap)}")
        for flag in _FORBIDDEN_TRUE_FLAGS:
            if value.get(flag) is True:
                raise ValueError(f"P11 fixture flag must not be true: {flag}")
        allowed = _as_tuple(value.get("expected_allowed_public_candidate_source_kinds") or ())
        if CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER not in allowed:
            raise ValueError("P11 fixture must allow low-information recovery source")
        if CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE not in allowed:
            raise ValueError("P11 fixture must allow bounded original repair source")
        if CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE not in allowed:
            raise ValueError("P11 fixture must allow complete self-repair source")
        if PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY in allowed:
            raise ValueError("P11 fixture must not allow diagnostic recovery surface as public source")
        for item in value.values():
            assert_p11_real_device_gate_recovery_fixture_meta_only(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            assert_p11_real_device_gate_recovery_fixture_meta_only(item)


__all__ = [
    "P11_ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS",
    "P11_FORBIDDEN_PUBLIC_FRAGMENTS",
    "P11_FORBIDDEN_SURFACE_CLASSES",
    "P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES",
    "P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION",
    "P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_SOURCE",
    "P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_VERSION",
    "RealDeviceGateRecoveryRegressionFixtureP11",
    "assert_p11_real_device_gate_recovery_fixture_meta_only",
    "build_p11_real_device_gate_recovery_regression_fixtures",
    "build_p11_real_device_product_quality_input_cases",
    "get_p11_fixture_by_id",
]
