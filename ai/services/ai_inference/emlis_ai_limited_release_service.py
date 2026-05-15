# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 7 staged-release controls for the internal limited Emlis Composer.

This module decides where the Phase 2/3 limited Composer may be auto-connected.
It does not generate user-facing text and it does not change API / DB contracts.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence

_ROLLOUT_STAGE_ENV_NAMES = (
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
    "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
    "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
)
_INTERNAL_USER_ENV_NAMES = (
    "COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    "EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
)

_STAGE_ALIASES = {
    "": "limited_cases",
    "default": "limited_cases",
    "limited": "limited_cases",
    "limited_case": "limited_cases",
    "limited_cases": "limited_cases",
    "limited-cases": "limited_cases",
    "scope": "limited_cases",
    "scope_eligible": "limited_cases",
    "internal": "internal",
    "staff": "internal",
    "qa": "internal",
    "tutorial": "tutorial",
    "tutorial_only": "tutorial",
    "tutorial-only": "tutorial",
    "all": "all",
    "public": "all",
    "enabled": "all",
    "on": "all",
    "off": "off",
    "disabled": "off",
    "none": "off",
}
_VALID_STAGES = {"off", "internal", "tutorial", "limited_cases", "all"}


@dataclass(frozen=True)
class LimitedComposerReleaseDecision:
    stage: str
    enabled: bool
    cohort: str = "blocked"
    reason_code: str = ""
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)
    internal_user: bool = False
    tutorial_case: bool = False
    limited_case: bool = False
    scope_status: str = ""
    scope_coverage: str = ""
    feature_flag_enabled: bool = False
    stage_source: str = "default"

    def as_meta(self) -> Dict[str, Any]:
        attempted = bool(self.enabled)
        return {
            "phase": 7,
            "version": "emlis.limited_composer_release.v1",
            "stage": self.stage,
            "enabled": bool(self.enabled),
            "attempted": attempted,
            "composer_attempt_allowed": attempted,
            "rollout_allowed": bool(self.enabled),
            "cohort": self.cohort,
            "reason_code": self.reason_code,
            "rejection_reasons": list(self.rejection_reasons),
            "internal_user": bool(self.internal_user),
            "tutorial_case": bool(self.tutorial_case),
            "limited_case": bool(self.limited_case),
            "scope_status": self.scope_status,
            "scope_coverage": self.scope_coverage,
            "feature_flag_enabled": bool(self.feature_flag_enabled),
            "stage_source": self.stage_source,
            "stage_env_names": list(_ROLLOUT_STAGE_ENV_NAMES),
            "rollout_decision": {
                "stage": self.stage,
                "enabled": bool(self.enabled),
                "attempted": attempted,
                "cohort": self.cohort,
                "reason_code": self.reason_code,
                "rejection_reasons": list(self.rejection_reasons),
                "internal_user": bool(self.internal_user),
                "tutorial_case": bool(self.tutorial_case),
                "limited_case": bool(self.limited_case),
                "scope_status": self.scope_status,
                "scope_coverage": self.scope_coverage,
                "feature_flag_enabled": bool(self.feature_flag_enabled),
                "stage_source": self.stage_source,
            },
            "metrics_fields": [
                "attempted",
                "passed",
                "rejected",
                "unavailable",
                "safety_blocked",
                "primary_reason",
                "coverage_group",
                "coverage_groups",
                "composer_model",
                "passed_rate_numerator",
                "passed_rate_denominator",
                "rejection_reasons",
            ],
            "step16_metric_fields": [
                "attempted",
                "passed",
                "rejected",
                "unavailable",
                "safety_blocked",
                "primary_reason",
                "coverage_group",
                "composer_model",
            ],
            "step16_metrics_version": "emlis.step16_rollout_metrics.v1",
        }


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_stage(value: Any) -> str:
    raw = _clean(value).lower().replace(" ", "_")
    return _STAGE_ALIASES.get(raw, raw if raw in _VALID_STAGES else "limited_cases")


def limited_composer_rollout_stage(env: Mapping[str, str] | None = None) -> tuple[str, str]:
    source = env if env is not None else os.environ
    for name in _ROLLOUT_STAGE_ENV_NAMES:
        if name in source and _clean(source.get(name)):
            return _normalize_stage(source.get(name)), name
    return "limited_cases", "default"


def _internal_user_ids(env: Mapping[str, str] | None = None) -> set[str]:
    source = env if env is not None else os.environ
    raw = ""
    for name in _INTERNAL_USER_ENV_NAMES:
        if _clean(source.get(name)):
            raw = _clean(source.get(name))
            break
    values = raw.replace("\n", ",").replace(";", ",").split(",")
    return {value.strip() for value in values if value.strip()}


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean(value).lower() in {"1", "true", "yes", "y", "on", "tutorial", "internal"}


def _is_internal_user(user_id: Any, *, current_input: Mapping[str, Any], env: Mapping[str, str] | None = None) -> bool:
    uid = _clean(user_id)
    if uid and uid in _internal_user_ids(env):
        return True
    for key in ("internal_test", "emlis_internal", "qa_user", "debug_internal"):
        if _boolish(current_input.get(key)):
            return True
    return False


def _is_tutorial_case(current_input: Mapping[str, Any]) -> bool:
    for key in ("is_tutorial", "tutorial", "tutorial_mode", "emlis_tutorial"):
        if _boolish(current_input.get(key)):
            return True
    joined = " ".join(
        _clean(current_input.get(key)).lower()
        for key in (
            "id",
            "source",
            "source_kind",
            "input_origin",
            "origin",
            "scenario_id",
            "selection_seed",
            "trace_id",
        )
    )
    return "tutorial" in joined


def _scope_status(scope: Any) -> str:
    if isinstance(scope, Mapping):
        return _clean(scope.get("scope_status"))
    return _clean(getattr(scope, "scope_status", ""))


def _scope_coverage(scope: Any) -> str:
    if isinstance(scope, Mapping):
        return _clean(scope.get("coverage_scope"))
    return _clean(getattr(scope, "coverage_scope", ""))


def _is_limited_case(scope: Any) -> bool:
    return _scope_status(scope) == "eligible"


def evaluate_limited_composer_release(
    *,
    user_id: Any,
    current_input: Mapping[str, Any] | None,
    limited_observation_scope: Any = None,
    feature_flag_enabled: bool = False,
    env: Mapping[str, str] | None = None,
) -> LimitedComposerReleaseDecision:
    payload = current_input if isinstance(current_input, Mapping) else {}
    stage, stage_source = limited_composer_rollout_stage(env)
    internal = _is_internal_user(user_id, current_input=payload, env=env)
    tutorial = _is_tutorial_case(payload)
    limited = _is_limited_case(limited_observation_scope)
    status = _scope_status(limited_observation_scope)
    coverage = _scope_coverage(limited_observation_scope)

    # Step10: safety is not a rollout failure.  It must stop before Composer
    # even when the feature flag is disabled or rollout would otherwise allow it.
    if status == "safety_blocked":
        return LimitedComposerReleaseDecision(
            stage=stage,
            enabled=False,
            cohort="blocked_safety",
            reason_code="safety_boundary_blocked",
            rejection_reasons=("limited_scope_safety_boundary", "safety_boundary"),
            internal_user=internal,
            tutorial_case=tutorial,
            limited_case=False,
            scope_status=status,
            scope_coverage=coverage,
            feature_flag_enabled=bool(feature_flag_enabled),
            stage_source=stage_source,
        )

    if not feature_flag_enabled:
        return LimitedComposerReleaseDecision(
            stage=stage,
            enabled=False,
            cohort="blocked",
            reason_code="feature_flag_disabled",
            rejection_reasons=("default_limited_composer_feature_disabled",),
            internal_user=internal,
            tutorial_case=tutorial,
            limited_case=limited,
            scope_status=status,
            scope_coverage=coverage,
            feature_flag_enabled=False,
            stage_source=stage_source,
        )
    if stage == "off":
        return LimitedComposerReleaseDecision(
            stage=stage,
            enabled=False,
            cohort="blocked",
            reason_code="rollout_stage_off",
            rejection_reasons=("limited_composer_rollout_off",),
            internal_user=internal,
            tutorial_case=tutorial,
            limited_case=limited,
            scope_status=status,
            scope_coverage=coverage,
            feature_flag_enabled=True,
            stage_source=stage_source,
        )

    if stage == "limited_cases" and not (internal or tutorial or limited) and status and status != "eligible":
        return LimitedComposerReleaseDecision(
            stage=stage,
            enabled=False,
            cohort="blocked_scope",
            reason_code="scope_limited_case_not_eligible",
            rejection_reasons=("limited_composer_scope_not_allowed", f"scope_{status}"),
            internal_user=internal,
            tutorial_case=tutorial,
            limited_case=limited,
            scope_status=status,
            scope_coverage=coverage,
            feature_flag_enabled=True,
            stage_source=stage_source,
        )

    allowed = False
    cohort = "blocked"
    reason = "rollout_stage_not_matched"
    if stage == "all":
        allowed = True
        cohort = "all"
        reason = "rollout_all"
    elif stage == "internal" and internal:
        allowed = True
        cohort = "internal"
        reason = "internal_user_allowed"
    elif stage == "tutorial" and (internal or tutorial):
        allowed = True
        cohort = "internal" if internal else "tutorial"
        reason = "tutorial_or_internal_allowed"
    elif stage == "limited_cases" and (internal or tutorial or limited):
        allowed = True
        cohort = "internal" if internal else ("tutorial" if tutorial else "limited_case")
        reason = "scope_limited_case_allowed" if limited else "internal_or_tutorial_allowed"

    rejections: tuple[str, ...] = () if allowed else ("limited_composer_rollout_not_allowed",)
    return LimitedComposerReleaseDecision(
        stage=stage,
        enabled=allowed,
        cohort=cohort,
        reason_code=reason,
        rejection_reasons=rejections,
        internal_user=internal,
        tutorial_case=tutorial,
        limited_case=limited,
        scope_status=status,
        scope_coverage=coverage,
        feature_flag_enabled=True,
        stage_source=stage_source,
    )


def build_phase7_rollout_metrics(
    *,
    release_decision: LimitedComposerReleaseDecision | None,
    observation_status: Any,
    rejection_reasons: Sequence[Any] | None = None,
) -> Dict[str, Any]:
    decision = release_decision or LimitedComposerReleaseDecision(stage="limited_cases", enabled=False)
    status = _clean(observation_status) or "unavailable"
    attempted = bool(decision.enabled)
    reasons = [str(item) for item in list(rejection_reasons or []) if str(item)]
    if not reasons and not attempted:
        reasons = list(decision.rejection_reasons or [])
    return {
        "phase": 7,
        "version": "emlis.limited_composer_rollout_metrics.v1",
        "stage": decision.stage,
        "cohort": decision.cohort,
        "attempted": attempted,
        "passed": attempted and status == "passed",
        "rejected": attempted and status == "rejected",
        "unavailable": attempted and status == "unavailable",
        "safety_blocked": attempted and status == "safety_blocked",
        "passed_rate_numerator": 1 if attempted and status == "passed" else 0,
        "passed_rate_denominator": 1 if attempted else 0,
        "observation_status": status,
        "rejection_reasons": reasons,
        "aggregation_key": f"{decision.stage}:{decision.cohort}",
    }


__all__ = [
    "LimitedComposerReleaseDecision",
    "limited_composer_rollout_stage",
    "evaluate_limited_composer_release",
    "build_phase7_rollout_metrics",
]
