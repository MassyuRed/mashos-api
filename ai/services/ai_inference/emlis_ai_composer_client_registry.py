# -*- coding: utf-8 -*-
from __future__ import annotations

"""Default Composer client registry for EmlisAI."""

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from emlis_ai_limited_composer_client import CocolonAPlanEquivalentComposerClient, CocolonLimitedComposerClient
from emlis_ai_a_plan_equivalent_composer_service import STEP19_A_PLAN_COMPOSER_MODEL

_TRUE_VALUES = {"1", "true", "yes", "y", "on", "enabled", "enable", "limited", "cocolon_limited"}
_FALSE_VALUES = {"0", "false", "no", "n", "off", "disabled", "disable", "none", "unavailable", ""}
_LIMITED_COMPOSER_FLAG_NAMES = (
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
    "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
    "COCOLON_LIMITED_COMPOSER_ENABLED",
    "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
    "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
)
_DEFAULT_COMPOSER_ENV_NAMES = (
    "COCOLON_EMLIS_DEFAULT_COMPOSER",
    "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
    "EMLIS_AI_DEFAULT_COMPOSER",
)
_DEFAULT_CLIENT_SOURCE = "cocolon_limited_composer"
_DEFAULT_A_PLAN_CLIENT_SOURCE = "cocolon_emlis_observation_composer_a1"
_DEFAULT_COMPOSER_MODEL = "cocolon_limited_composer.v1"
_DEFAULT_A_PLAN_COMPOSER_MODEL = STEP19_A_PLAN_COMPOSER_MODEL
_A_PLAN_COMPOSER_ALIASES = {
    "a_plan",
    "a-plan",
    "a1",
    "a_1",
    "a-plan-equivalent",
    "a_plan_equivalent",
    "cocolon_emlis_observation_composer_a1",
    "cocolon_emlis_observation_composer.a1",
    "cocolon_emlis_observation_composer.a1.v1",
}
_LIMITED_COMPOSER_ALIASES = {"limited", "cocolon_limited", "cocolon_limited_composer"}


@dataclass(frozen=True)
class ComposerClientResolution:
    composer_client: Optional[Any]
    explicit_client_used: bool
    default_client_used: bool
    default_limited_enabled: bool
    resolution_source: str
    composer_model: str = ""
    safety_blocked: bool = False
    release_allowed: Optional[bool] = None
    release_meta: Mapping[str, Any] | None = None
    flag_state: Mapping[str, Any] | None = None
    rejection_reasons: tuple[str, ...] = ()

    def as_meta(self) -> dict[str, Any]:
        composer_attempted = False if self.safety_blocked else bool(self.explicit_client_used or self.default_client_used)
        if self.explicit_client_used:
            connection_status = "provided_client"
            stop_stage = "provided"
        elif self.default_client_used:
            connection_status = "default_client_resolved"
            stop_stage = "default_resolved"
        elif self.safety_blocked:
            connection_status = "blocked_safety"
            stop_stage = "safety"
        elif not self.default_limited_enabled:
            connection_status = "blocked_feature_flag"
            stop_stage = "flag"
        elif self.release_allowed is False:
            reason_code = ""
            cohort = ""
            release_reasons = []
            if isinstance(self.release_meta, Mapping):
                reason_code = str(self.release_meta.get("reason_code") or "")
                cohort = str(self.release_meta.get("cohort") or "")
                release_reasons = [str(item or "") for item in list(self.release_meta.get("rejection_reasons") or [])]
            if reason_code.startswith("scope_") or cohort == "blocked_scope" or any(item.startswith("scope_") for item in release_reasons):
                connection_status = "blocked_scope"
                stop_stage = "scope"
            else:
                connection_status = "blocked_rollout"
                stop_stage = "rollout"
        else:
            connection_status = "not_resolved"
            stop_stage = "unknown"
        return {
            "default_registry_version": "emlis.default_composer_registry.v2",
            "feature_flag_names": list(_LIMITED_COMPOSER_FLAG_NAMES),
            "feature_flag_state": dict(self.flag_state or {}),
            "explicit_client_used": bool(self.explicit_client_used),
            "explicit_client_provided": bool(self.explicit_client_used),
            "default_client_used": bool(self.default_client_used),
            "default_connection_active": bool(self.default_client_used),
            "default_limited_enabled": bool(self.default_limited_enabled),
            "feature_enabled": bool(self.default_limited_enabled),
            "feature_flag_enabled": bool(self.default_limited_enabled),
            "resolution_source": str(self.resolution_source or ""),
            "source": str(self.resolution_source or ""),
            "resolved_client_name": type(self.composer_client).__name__ if self.composer_client is not None else "",
            "resolved_client_class": type(self.composer_client).__name__ if self.composer_client is not None else "",
            "composer_model": str(self.composer_model or ""),
            "default_client_model": str(self.composer_model or ""),
            "safety_blocked": bool(self.safety_blocked),
            "release_allowed": self.release_allowed,
            "release_gate": dict(self.release_meta or {}),
            "phase7_rollout_gate": dict(self.release_meta or {}),
            "connection_status": connection_status,
            "pre_connection_stop_stage": stop_stage,
            "registry_attempted": True,
            "composer_attempted": composer_attempted,
            "default_client_resolved": bool(self.default_client_used),
            "blocked_before_composer": bool(not composer_attempted),
            "default_composer_resolution": {
                "resolution_source": str(self.resolution_source or ""),
                "explicit_client_used": bool(self.explicit_client_used),
                "default_client_used": bool(self.default_client_used),
                "default_connection_active": bool(self.default_client_used),
                "resolved_client_class": type(self.composer_client).__name__ if self.composer_client is not None else "",
                "composer_model": str(self.composer_model or ""),
                "release_allowed": self.release_allowed,
                "safety_blocked": bool(self.safety_blocked),
                "connection_status": connection_status,
                "pre_connection_stop_stage": stop_stage,
                "composer_attempted": composer_attempted,
                "default_client_resolved": bool(self.default_client_used),
            },
            "rejection_reasons": list(self.rejection_reasons or ()),
        }


def _env_value(env: Mapping[str, str], name: str) -> str:
    return str(env.get(name) or "").strip().lower()


def _truthy(value: Any) -> bool:
    normalized = str(value or "").strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return False


def _requested_default_composer(env: Mapping[str, str]) -> dict[str, Any]:
    for name in _DEFAULT_COMPOSER_ENV_NAMES:
        if name not in env:
            continue
        raw = str(env.get(name) or "")
        normalized = raw.strip().lower().replace(" ", "_")
        if normalized in _A_PLAN_COMPOSER_ALIASES:
            return {
                "requested_composer": "a_plan_equivalent",
                "requested_composer_model": _DEFAULT_A_PLAN_COMPOSER_MODEL,
                "requested_source": _DEFAULT_A_PLAN_CLIENT_SOURCE,
                "default_composer_matched_name": name,
                "default_composer_matched_value": raw,
            }
        if normalized in _LIMITED_COMPOSER_ALIASES:
            return {
                "requested_composer": "limited",
                "requested_composer_model": _DEFAULT_COMPOSER_MODEL,
                "requested_source": _DEFAULT_CLIENT_SOURCE,
                "default_composer_matched_name": name,
                "default_composer_matched_value": raw,
            }
    return {
        "requested_composer": "limited",
        "requested_composer_model": _DEFAULT_COMPOSER_MODEL,
        "requested_source": _DEFAULT_CLIENT_SOURCE,
        "default_composer_matched_name": "",
        "default_composer_matched_value": "",
    }


def _limited_default_composer_flag_scan(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    flag_values = {name: str(source.get(name) or "") for name in _LIMITED_COMPOSER_FLAG_NAMES}
    default_composer_values = {name: str(source.get(name) or "") for name in _DEFAULT_COMPOSER_ENV_NAMES}
    requested = _requested_default_composer(source)
    for name in _LIMITED_COMPOSER_FLAG_NAMES:
        if name in source:
            raw = str(source.get(name) or "")
            return {
                "enabled": _truthy(raw),
                "matched_name": name,
                "matched_value": raw,
                "source_kind": "feature_flag",
                "source": name,
                "explicitly_configured": True,
                "flag_values": flag_values,
                "default_composer_values": default_composer_values,
                **requested,
            }
    for name in _DEFAULT_COMPOSER_ENV_NAMES:
        if name in source:
            raw = str(source.get(name) or "")
            normalized = _env_value(source, name).replace(" ", "_")
            enabled = normalized in _LIMITED_COMPOSER_ALIASES or normalized in _A_PLAN_COMPOSER_ALIASES
            return {
                "enabled": enabled,
                "matched_name": name,
                "matched_value": raw,
                "source_kind": "default_composer_env",
                "source": name,
                "explicitly_configured": True,
                "flag_values": flag_values,
                "default_composer_values": default_composer_values,
                **requested,
            }
    return {
        "enabled": False,
        "matched_name": "",
        "matched_value": "",
        "source_kind": "default",
        "source": "default",
        "explicitly_configured": False,
        "flag_values": flag_values,
        "default_composer_values": default_composer_values,
        **requested,
    }


def limited_default_composer_enabled(env: Mapping[str, str] | None = None) -> bool:
    return bool(_limited_default_composer_flag_scan(env).get("enabled"))


def default_limited_composer_enabled(env: Mapping[str, str] | None = None) -> bool:
    return limited_default_composer_enabled(env)


def default_composer_flag_state(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    scan = _limited_default_composer_flag_scan(env)
    set_flags = {
        name: str(source.get(name) or "")
        for name in (*_LIMITED_COMPOSER_FLAG_NAMES, *_DEFAULT_COMPOSER_ENV_NAMES)
        if str(source.get(name) or "").strip()
    }
    return {
        "version": "emlis.default_composer_flag_state.v1",
        "flag_names": list(_LIMITED_COMPOSER_FLAG_NAMES),
        "default_composer_env_names": list(_DEFAULT_COMPOSER_ENV_NAMES),
        "enabled": bool(scan.get("enabled")),
        "set_flags": set_flags,
        "flag_values": dict(scan.get("flag_values") or {}),
        "default_composer_values": dict(scan.get("default_composer_values") or {}),
        "matched_name": str(scan.get("matched_name") or ""),
        "matched_value": str(scan.get("matched_value") or ""),
        "source_kind": str(scan.get("source_kind") or ""),
        "source": str(scan.get("source") or ""),
        "explicitly_configured": bool(scan.get("explicitly_configured")),
        "requested_composer": str(scan.get("requested_composer") or "limited"),
        "requested_composer_model": str(scan.get("requested_composer_model") or _DEFAULT_COMPOSER_MODEL),
        "requested_source": str(scan.get("requested_source") or _DEFAULT_CLIENT_SOURCE),
        "default_composer_matched_name": str(scan.get("default_composer_matched_name") or ""),
        "default_composer_matched_value": str(scan.get("default_composer_matched_value") or ""),
        "step19_a_plan_composer_requested": str(scan.get("requested_composer") or "") == "a_plan_equivalent",
    }


def resolve_emlis_ai_composer_client(
    *,
    composer_client: Any = None,
    safety_requires_block: bool = False,
    env: Mapping[str, str] | None = None,
    release_allowed: Optional[bool] = None,
    release_meta: Mapping[str, Any] | None = None,
) -> ComposerClientResolution:
    enabled = limited_default_composer_enabled(env)
    flag_state = default_composer_flag_state(env)
    if safety_requires_block:
        return ComposerClientResolution(
            composer_client=None,
            explicit_client_used=False,
            default_client_used=False,
            default_limited_enabled=enabled,
            resolution_source="none",
            safety_blocked=True,
            release_allowed=release_allowed,
            release_meta=release_meta,
            flag_state=flag_state,
            rejection_reasons=("safety_boundary", "composer_prevented_by_safety_boundary"),
        )
    if composer_client is not None:
        return ComposerClientResolution(
            composer_client=composer_client,
            explicit_client_used=True,
            default_client_used=False,
            default_limited_enabled=enabled,
            resolution_source="provided",
            composer_model=str(getattr(composer_client, "composer_model", "") or "provided"),
            safety_blocked=False,
            release_allowed=release_allowed,
            release_meta=release_meta,
            flag_state=flag_state,
        )
    if not enabled:
        return ComposerClientResolution(
            composer_client=None,
            explicit_client_used=False,
            default_client_used=False,
            default_limited_enabled=False,
            resolution_source="none",
            release_allowed=release_allowed,
            release_meta=release_meta,
            flag_state=flag_state,
            rejection_reasons=("default_limited_composer_feature_disabled",),
        )
    if release_allowed is False:
        reason_code = str(release_meta.get("reason_code") or "") if isinstance(release_meta, Mapping) else ""
        cohort = str(release_meta.get("cohort") or "") if isinstance(release_meta, Mapping) else ""
        scope_blocked = bool(reason_code.startswith("scope_") or cohort == "blocked_scope")
        reasons = [] if scope_blocked else ["limited_composer_rollout_not_allowed"]
        if isinstance(release_meta, Mapping):
            for item in list(release_meta.get("rejection_reasons") or []):
                text = str(item or "").strip()
                if text and text not in reasons:
                    reasons.append(text)
        if scope_blocked and "limited_composer_rollout_not_allowed" not in reasons:
            reasons.append("limited_composer_rollout_not_allowed")
        if scope_blocked and not reasons:
            reasons.append("scope_limited_case_not_eligible")
        return ComposerClientResolution(
            composer_client=None,
            explicit_client_used=False,
            default_client_used=False,
            default_limited_enabled=True,
            resolution_source="none",
            release_allowed=False,
            release_meta=release_meta,
            flag_state=flag_state,
            rejection_reasons=tuple(reasons),
        )
    requested = str(flag_state.get("requested_composer") or "limited")
    if requested == "a_plan_equivalent":
        client = CocolonAPlanEquivalentComposerClient()
        source = _DEFAULT_A_PLAN_CLIENT_SOURCE
        default_model = _DEFAULT_A_PLAN_COMPOSER_MODEL
    else:
        client = CocolonLimitedComposerClient()
        source = _DEFAULT_CLIENT_SOURCE
        default_model = _DEFAULT_COMPOSER_MODEL
    return ComposerClientResolution(
        composer_client=client,
        explicit_client_used=False,
        default_client_used=True,
        default_limited_enabled=True,
        resolution_source=source,
        composer_model=str(getattr(client, "composer_model", default_model) or default_model),
        release_allowed=release_allowed,
        release_meta=release_meta,
        flag_state=flag_state,
    )


def resolve_default_emlis_composer_client(
    *,
    composer_client: Any = None,
    safety_requires_block: bool = False,
    env: Mapping[str, str] | None = None,
    release_allowed: Optional[bool] = None,
    release_meta: Mapping[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    resolution = resolve_emlis_ai_composer_client(
        composer_client=composer_client,
        safety_requires_block=safety_requires_block,
        env=env,
        release_allowed=release_allowed,
        release_meta=release_meta,
    )
    return resolution.composer_client, resolution.as_meta()


__all__ = [
    "ComposerClientResolution",
    "limited_default_composer_enabled",
    "default_limited_composer_enabled",
    "default_composer_flag_state",
    "resolve_emlis_ai_composer_client",
    "resolve_default_emlis_composer_client",
]
