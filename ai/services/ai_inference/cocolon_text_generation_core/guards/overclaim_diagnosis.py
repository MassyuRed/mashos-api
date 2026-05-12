# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic overclaim and diagnosis wording guard.

This guard only inspects a candidate text.  It does not create text and does
not change any EmlisAI / Piece / Analysis public contract.
"""

import re
from typing import Any, Mapping

from cocolon_text_generation_core.guards.base import GuardResult, make_guard_result
from cocolon_text_generation_core.policies import CORE_ID_ANALYSIS

OVERCLAIM_DIAGNOSIS_GUARD_NAME = "cocolon_text_generation_core.guards.overclaim_diagnosis.v1"

REJECTION_DIAGNOSIS_SURFACE = "diagnosis_surface"
REJECTION_PERSONALITY_ASSERTION = "personality_assertion"
REJECTION_ANALYSIS_STRICT_ASSERTION = "analysis_strict_assertion"
REJECTION_DEEP_WISH_OVERCLAIM = "deep_wish_overclaim"
REJECTION_CAUSAL_ASSERTION = "causal_assertion"
REJECTION_ADVICE_ASSERTION = "advice_assertion"
REJECTION_GENERAL_THEORY = "general_theory"

QUALITY_FLAG_OVERCLAIM_DIAGNOSIS_FAILED = "overclaim_diagnosis_failed"

# Compatibility aliases for draft names used in planning documents.
REJECTION_DIAGNOSIS_WORDING = REJECTION_DIAGNOSIS_SURFACE
REJECTION_PERSONALITY_LOCK_IN = REJECTION_PERSONALITY_ASSERTION
REJECTION_INNER_TRUTH_CLAIM = REJECTION_DEEP_WISH_OVERCLAIM
REJECTION_UNSUPPORTED_GENERALISATION = REJECTION_GENERAL_THEORY
REJECTION_ANALYSIS_ASSERTIVE_ADDRESS = REJECTION_ANALYSIS_STRICT_ASSERTION
REJECTION_OVERCLAIM_SECOND_PERSON_ASSERTION = REJECTION_ANALYSIS_STRICT_ASSERTION

_DIAGNOSIS_RE = re.compile(
    r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|自律神経|依存症|PTSD|医療|心理療法|心理学的には"
)
_PERSONALITY_RE = re.compile(
    r"(?:あなた|その人|本人)(?:は|の)(?:[^。！？!?]{0,28})?(?:性格|人格|本質|タイプ|こういう人|弱い人|強い人|怠け|甘え)"
)
_INNER_TRUTH_RE = re.compile(
    r"本当の願い|本当は[^。！？!?]{0,24}(?:望んで|求めて|思って|願って)|本心|心の奥|無意識|潜在意識"
)
_GENERALISATION_RE = re.compile(
    r"(?:多くの人|誰でも|普通は|一般的に|人はみんな|よくあること)(?:[^。！？!?]{0,36})(?:です|あります|なります)"
)
_ADVICE_RE = re.compile(
    r"(?:必要があります|すべきです|するべきです|しなければなりません|正解です|間違いです)"
)
_CAUSAL_RE = re.compile(
    r"(?:だから|そのため|原因は)(?:[^。！？!?]{0,40})(?:です|あります|なっています)"
)
_ANALYSIS_ASSERTIVE_RE = re.compile(
    r"あなた(?:は|の)(?:[^。！？!?]{0,40})(?:パターンです|人です|タイプです|性格です|本質です|決まっています|傾向があります)"
)
_NEGATED_SAFETY_NOTE_RE = re.compile(
    r"(?:診断|断定|医療|心理診断|心理学的)(?:[^。！？!?]{0,36})(?:ではありません|目的ではありません|目的としたものではありません|しません|していません)"
)


class OverclaimPolicy(dict):
    """Small compatibility policy container for guard callers."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


def _strict_analysis(
    policy: Mapping[str, Any] | None = None,
    core_id: Any = "",
    strict: bool | None = None,
) -> bool:
    if strict is not None:
        return bool(strict)
    meta = policy if isinstance(policy, Mapping) else {}
    if bool(meta.get("strict")) or bool(meta.get("analysis_strict")):
        return True
    strictness = str(meta.get("strictness") or "").strip().lower()
    resolved_core = str(core_id or meta.get("core_id") or "").strip().lower()
    return strictness in {"analysis", "strict", "high"} or resolved_core == CORE_ID_ANALYSIS


def guard_overclaim_diagnosis(
    comment_text: Any,
    *,
    policy: Mapping[str, Any] | None = None,
    core_id: Any = "",
    strict: bool | None = None,
) -> GuardResult:
    text = str(comment_text or "").strip()
    # Analysis reports may include safety notes such as 「診断や断定を目的としたものではありません」.
    # Those notes are allowed because they explicitly negate diagnosis/lock-in; remove
    # them only from the scan surface while keeping the original text untouched.
    scan_text = _NEGATED_SAFETY_NOTE_RE.sub("", text)
    reasons: list[str] = []
    matched: list[str] = []

    checks = (
        (REJECTION_DIAGNOSIS_SURFACE, _DIAGNOSIS_RE),
        (REJECTION_PERSONALITY_ASSERTION, _PERSONALITY_RE),
        (REJECTION_DEEP_WISH_OVERCLAIM, _INNER_TRUTH_RE),
        (REJECTION_GENERAL_THEORY, _GENERALISATION_RE),
        (REJECTION_ADVICE_ASSERTION, _ADVICE_RE),
    )
    for reason, pattern in checks:
        if pattern.search(scan_text):
            reasons.append(reason)
            matched.append(pattern.pattern)

    analysis_strict = _strict_analysis(policy, core_id, strict)
    if analysis_strict and _ANALYSIS_ASSERTIVE_RE.search(scan_text):
        reasons.append(REJECTION_ANALYSIS_STRICT_ASSERTION)
        matched.append(_ANALYSIS_ASSERTIVE_RE.pattern)
    if analysis_strict and _CAUSAL_RE.search(scan_text) and "観測" not in scan_text:
        reasons.append(REJECTION_CAUSAL_ASSERTION)
        matched.append(_CAUSAL_RE.pattern)

    return make_guard_result(
        guard_name=OVERCLAIM_DIAGNOSIS_GUARD_NAME,
        reasons=reasons,
        quality_flags=(QUALITY_FLAG_OVERCLAIM_DIAGNOSIS_FAILED,) if reasons else (),
        matched_texts=matched,
        meta={"analysis_strict": analysis_strict, "safety_note_removed": scan_text != text},
    )


class OverclaimDiagnosisGuard:
    guard_name = OVERCLAIM_DIAGNOSIS_GUARD_NAME

    def __init__(self, policy: Mapping[str, Any] | None = None) -> None:
        self.policy = policy if isinstance(policy, Mapping) else {}

    def evaluate(self, comment_text: Any, **kwargs: Any) -> GuardResult:
        policy = kwargs.pop("policy", self.policy)
        return guard_overclaim_diagnosis(comment_text, policy=policy, **kwargs)

    def check(self, comment_text: Any, **kwargs: Any) -> GuardResult:
        return self.evaluate(comment_text, **kwargs)


evaluate_overclaim_diagnosis = guard_overclaim_diagnosis
judge_overclaim_diagnosis = guard_overclaim_diagnosis
check_overclaim_diagnosis = guard_overclaim_diagnosis

__all__ = [
    "OVERCLAIM_DIAGNOSIS_GUARD_NAME",
    "OverclaimDiagnosisGuard",
    "OverclaimPolicy",
    "guard_overclaim_diagnosis",
    "evaluate_overclaim_diagnosis",
    "judge_overclaim_diagnosis",
    "check_overclaim_diagnosis",
    "REJECTION_DIAGNOSIS_SURFACE",
    "REJECTION_PERSONALITY_ASSERTION",
    "REJECTION_ANALYSIS_STRICT_ASSERTION",
    "REJECTION_DEEP_WISH_OVERCLAIM",
    "REJECTION_CAUSAL_ASSERTION",
    "REJECTION_ADVICE_ASSERTION",
    "REJECTION_GENERAL_THEORY",
    "REJECTION_DIAGNOSIS_WORDING",
    "REJECTION_PERSONALITY_LOCK_IN",
    "REJECTION_INNER_TRUTH_CLAIM",
    "REJECTION_UNSUPPORTED_GENERALISATION",
    "REJECTION_ANALYSIS_ASSERTIVE_ADDRESS",
]
