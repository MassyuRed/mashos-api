# -*- coding: utf-8 -*-
from __future__ import annotations

"""Compatibility import path for Step 9 Observation Surface Realizer.

The implementation lives in ``emlis_ai_observation_surface_realizer_tone``.
This short path is intentionally a re-export only, so Step 9 does not create a
second surface implementation or alter ReplyEnvelope / Display Gate behavior.
"""

from emlis_ai_observation_surface_realizer_tone import (  # noqa: F401
    OBSERVATION_SURFACE_REALIZER_TONE_SCHEMA_VERSION as OBSERVATION_SURFACE_REALIZATION_SCHEMA_VERSION,
    OBSERVATION_SURFACE_REALIZER_TONE_STEP as OBSERVATION_SURFACE_REALIZER_STEP,
    OBSERVATION_SURFACE_REALIZER_TONE_VERSION as OBSERVATION_SURFACE_REALIZER_VERSION,
    OBSERVATION_TEMPLATE_GUARD_VERSION,
    OBSERVATION_TONE_POLICY_VERSION,
    QUESTION_SURFACE_KIND_WHAT_CHANGED,
    QUESTION_SURFACE_KIND_WHAT_HAPPENED,
    QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY,
    QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY,
    ObservationSurfaceLine,
    ObservationSurfaceRealization,
    assert_observation_surface_realizer_contract,
    build_emlis_ai_observation_surface,
    build_observation_surface_realizer,
    build_observation_surface_realizer_contract_meta,
    build_observation_surface_realizer_meta,
    build_observation_surface_template_report,
    build_observation_surface_tone_report,
    dump_observation_surface_realizer,
    realize_eligible_observation_surface,
    realize_low_information_observation_surface,
    realize_observation_surface,
    select_observation_question_ending,
)

__all__ = [
    "OBSERVATION_SURFACE_REALIZATION_SCHEMA_VERSION",
    "OBSERVATION_SURFACE_REALIZER_STEP",
    "OBSERVATION_SURFACE_REALIZER_VERSION",
    "OBSERVATION_TEMPLATE_GUARD_VERSION",
    "OBSERVATION_TONE_POLICY_VERSION",
    "QUESTION_SURFACE_KIND_WHAT_CHANGED",
    "QUESTION_SURFACE_KIND_WHAT_HAPPENED",
    "QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY",
    "QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY",
    "ObservationSurfaceLine",
    "ObservationSurfaceRealization",
    "assert_observation_surface_realizer_contract",
    "build_emlis_ai_observation_surface",
    "build_observation_surface_realizer",
    "build_observation_surface_realizer_contract_meta",
    "build_observation_surface_realizer_meta",
    "build_observation_surface_template_report",
    "build_observation_surface_tone_report",
    "dump_observation_surface_realizer",
    "realize_eligible_observation_surface",
    "realize_low_information_observation_surface",
    "realize_observation_surface",
    "select_observation_question_ending",
]
