# -*- coding: utf-8 -*-
from __future__ import annotations

"""Default Composer client registry for EmlisAI."""

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient

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
_DEFAULT_COMPOSER_MODEL = "cocolon_limited_composer.v1"


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
    rejection_reasons: tuple[str, ...] = ()

    def as_meta(self) -> dict[str, Any]:
        return {
            "default_registry_version": "emlis.default_composer_registry.v2",
            "feature_flag_names": list(_LIMITED_COMPOSER_FLAG_NAMES),
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


def limited_default_composer_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = env if env is not None else os.environ
    for name in _LIMITED_COMPOSER_FLAG_NAMES:
        if name in source:
            return _truthy(source.get(name))
    for name in _DEFAULT_COMPOSER_ENV_NAMES:
        if name in source:
            return _env_value(source, name) in {"limited", "cocolon_limited", "cocolon_limited_composer"}
    return False


def default_limited_composer_enabled(env: Mapping[str, str] | None = None) -> bool:
    return limited_default_composer_enabled(env)


def default_composer_flag_state(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    set_flags = {
        name: str(source.get(name) or "")
        for name in (*_LIMITED_COMPOSER_FLAG_NAMES, *_DEFAULT_COMPOSER_ENV_NAMES)
        if str(source.get(name) or "").strip()
    }
    return {
        "flag_names": list(_LIMITED_COMPOSER_FLAG_NAMES),
        "default_composer_env_names": list(_DEFAULT_COMPOSER_ENV_NAMES),
        "enabled": limited_default_composer_enabled(env),
        "set_flags": set_flags,
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
    if composer_client is not None:
        return ComposerClientResolution(
            composer_client=composer_client,
            explicit_client_used=True,
            default_client_used=False,
            default_limited_enabled=enabled,
            resolution_source="provided",
            composer_model=str(getattr(composer_client, "composer_model", "") or "provided"),
            safety_blocked=bool(safety_requires_block),
            release_allowed=release_allowed,
            release_meta=release_meta,
        )
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
            rejection_reasons=("safety_boundary",),
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
            rejection_reasons=("default_limited_composer_feature_disabled",),
        )
    if release_allowed is False:
        reasons = ["limited_composer_rollout_not_allowed"]
        if isinstance(release_meta, Mapping):
            for item in list(release_meta.get("rejection_reasons") or []):
                text = str(item or "").strip()
                if text and text not in reasons:
                    reasons.append(text)
        return ComposerClientResolution(
            composer_client=None,
            explicit_client_used=False,
            default_client_used=False,
            default_limited_enabled=True,
            resolution_source="none",
            release_allowed=False,
            release_meta=release_meta,
            rejection_reasons=tuple(reasons),
        )
    client = CocolonLimitedComposerClient()
    return ComposerClientResolution(
        composer_client=client,
        explicit_client_used=False,
        default_client_used=True,
        default_limited_enabled=True,
        resolution_source=_DEFAULT_CLIENT_SOURCE,
        composer_model=str(getattr(client, "composer_model", _DEFAULT_COMPOSER_MODEL) or _DEFAULT_COMPOSER_MODEL),
        release_allowed=release_allowed,
        release_meta=release_meta,
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
