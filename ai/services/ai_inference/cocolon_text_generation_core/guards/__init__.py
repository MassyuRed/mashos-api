# -*- coding: utf-8 -*-
from __future__ import annotations

"""Common guard layer for Cocolon Text Generation Core."""

from .base import GuardReport, GuardResult, combine_guard_reports, combine_guard_results, merge_guard_reports
from .grounding import GroundingGuard, check_grounding, evaluate_grounding, guard_grounding, judge_grounding
from .japanese_coherence import (
    JapaneseCoherenceGuard,
    check_japanese_coherence,
    evaluate_japanese_coherence,
    guard_japanese_coherence,
    judge_japanese_coherence,
)
from .must_keep_coverage import (
    MustKeepCoverageGuard,
    check_must_keep_coverage,
    evaluate_must_keep_coverage,
    guard_must_keep_coverage,
    guard_must_keep_coverage_for_payload,
    judge_must_keep_coverage,
)
from .overclaim_diagnosis import (
    OverclaimDiagnosisGuard,
    OverclaimPolicy,
    check_overclaim_diagnosis,
    evaluate_overclaim_diagnosis,
    guard_overclaim_diagnosis,
    judge_overclaim_diagnosis,
)
from .template_echo import TemplateEchoGuard, check_template_echo, evaluate_template_echo, guard_template_echo, judge_template_echo

__all__ = [
    "GuardReport",
    "GuardResult",
    "GroundingGuard",
    "JapaneseCoherenceGuard",
    "MustKeepCoverageGuard",
    "OverclaimDiagnosisGuard",
    "OverclaimPolicy",
    "TemplateEchoGuard",
    "check_grounding",
    "check_japanese_coherence",
    "check_must_keep_coverage",
    "check_overclaim_diagnosis",
    "check_template_echo",
    "combine_guard_reports",
    "combine_guard_results",
    "merge_guard_reports",
    "evaluate_grounding",
    "evaluate_japanese_coherence",
    "evaluate_must_keep_coverage",
    "evaluate_overclaim_diagnosis",
    "evaluate_template_echo",
    "guard_grounding",
    "guard_japanese_coherence",
    "guard_must_keep_coverage",
    "guard_must_keep_coverage_for_payload",
    "guard_overclaim_diagnosis",
    "guard_template_echo",
    "judge_grounding",
    "judge_japanese_coherence",
    "judge_must_keep_coverage",
    "judge_overclaim_diagnosis",
    "judge_template_echo",
]
