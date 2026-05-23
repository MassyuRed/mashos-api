# -*- coding: utf-8 -*-
from __future__ import annotations

"""Baseline red fixtures for EmlisAI runtime surface pre-return gate.

These fixtures intentionally lock *bad public surfaces* as examples that must
never be allowed to pass display pre-return quality.  They do not lock a good
replacement sentence and are not runtime special cases.
"""

from dataclasses import dataclass
from typing import Any

RUNTIME_SURFACE_RED_FIXTURE_VERSION = "emlis.runtime_surface_red_fixtures.v1"


@dataclass(frozen=True)
class RuntimeSurfaceRedFixture:
    fixture_id: str
    public_body: str
    composer_meta: dict[str, Any]
    expected_rejection_reasons: tuple[str, ...]
    forbidden_surface_markers: tuple[str, ...]
    expected_action: str = "rerender_shallow_v2"
    expected_public_status_after_step1: str = "not_passed"


_SHALLOW_CURRENT_INPUT_CORE_META: dict[str, Any] = {
    "profile_key": "current_input_core",
    "coverage_scope": "current_input_core",
    "shallow_observation_path": True,
    "composer_source": "ai_generated",
}

RUNTIME_SURFACE_BASELINE_RED_FIXTURES: tuple[RuntimeSurfaceRedFixture, ...] = (
    RuntimeSurfaceRedFixture(
        fixture_id="runtime_surface_red_malformed_koto_center_connector_stack",
        public_body=(
            "Emlisです。\n"
            "まだないかことが中心にあります。\n"
            "その中でも、しれないどれことも見えています。\n"
            "その中でも、好きでやってるやつが多いから上手になせなくてことも重なっています。"
        ),
        composer_meta=dict(_SHALLOW_CURRENT_INPUT_CORE_META),
        expected_rejection_reasons=(
            "surface_template_major",
            "generic_center_phrase",
            "same_connector_run",
            "malformed_phrase_unit",
        ),
        forbidden_surface_markers=(
            "まだないかこと",
            "しれないどれこと",
            "上手になせなくてこと",
            "その中でも",
            "が中心にあります",
        ),
    ),
    RuntimeSurfaceRedFixture(
        fixture_id="runtime_surface_red_temporal_koto_adjective_koto_center",
        public_body=(
            "Emlisです。\n"
            "今までことが中心にあります。\n"
            "その中でも、大丈夫ことも見えています。\n"
            "その中でも、創作をする時にリアルさを求めることも重なっています。"
        ),
        composer_meta=dict(_SHALLOW_CURRENT_INPUT_CORE_META),
        expected_rejection_reasons=(
            "surface_template_major",
            "generic_center_phrase",
            "surface_grammar_warning",
            "malformed_phrase_unit",
        ),
        forbidden_surface_markers=(
            "今までこと",
            "大丈夫こと",
            "その中でも",
            "が中心にあります",
        ),
    ),
    RuntimeSurfaceRedFixture(
        fixture_id="runtime_surface_red_center_phrase_single_malformed_koto",
        public_body=(
            "Emlisです。\n"
            "今までことが中心にあります。"
        ),
        composer_meta=dict(_SHALLOW_CURRENT_INPUT_CORE_META),
        expected_rejection_reasons=(
            "surface_template_major",
            "generic_center_phrase",
            "malformed_phrase_unit",
        ),
        forbidden_surface_markers=("今までこと", "が中心にあります"),
    ),
    RuntimeSurfaceRedFixture(
        fixture_id="runtime_surface_red_connector_repeat_without_center",
        public_body=(
            "Emlisです。\n"
            "その中でも、大丈夫ことも見えています。\n"
            "その中でも、創作をする時にリアルさを求めることも重なっています。"
        ),
        composer_meta=dict(_SHALLOW_CURRENT_INPUT_CORE_META),
        expected_rejection_reasons=(
            "same_connector_run",
            "same_connector_repetition",
            "surface_connector_repetition",
            "malformed_phrase_unit",
        ),
        forbidden_surface_markers=("大丈夫こと", "その中でも"),
    ),
    RuntimeSurfaceRedFixture(
        fixture_id="runtime_surface_red_te_form_koto_single_line",
        public_body=(
            "Emlisです。\n"
            "上手になせなくてことも重なっています。"
        ),
        composer_meta=dict(_SHALLOW_CURRENT_INPUT_CORE_META),
        expected_rejection_reasons=(
            "malformed_phrase_unit",
            "malformed_nominalization_te_form_fragment",
        ),
        forbidden_surface_markers=("上手になせなくてこと",),
    ),
)


def iter_runtime_surface_baseline_red_fixtures() -> tuple[RuntimeSurfaceRedFixture, ...]:
    return RUNTIME_SURFACE_BASELINE_RED_FIXTURES


__all__ = [
    "RUNTIME_SURFACE_BASELINE_RED_FIXTURES",
    "RUNTIME_SURFACE_RED_FIXTURE_VERSION",
    "RuntimeSurfaceRedFixture",
    "iter_runtime_surface_baseline_red_fixtures",
]
