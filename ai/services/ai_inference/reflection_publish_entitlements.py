# -*- coding: utf-8 -*-
"""Legacy reflection publish entitlements compat facade.

Runtime body now lives in ``piece_publish_entitlements``. This file is intentionally
kept as a thin compatibility import path until public legacy contracts and DB
physical names are retired in a separate release step.
"""

from __future__ import annotations

import sys
import types

import piece_publish_entitlements as _current


def _export_public_names() -> list[str]:
    names = getattr(_current, "__all__", None)
    if names is None:
        names = [name for name in dir(_current) if not name.startswith("__")]
    out: list[str] = []
    for name in names:
        if not isinstance(name, str) or not name:
            continue
        try:
            globals()[name] = getattr(_current, name)
        except AttributeError:
            continue
        out.append(name)
    return out


__all__ = _export_public_names()


class _CompatModule(types.ModuleType):
    def __getattr__(self, name: str):
        return getattr(_current, name)

    def __setattr__(self, name: str, value):
        if not name.startswith("__"):
            try:
                setattr(_current, name, value)
            except Exception:
                pass
        return super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CompatModule


def __getattr__(name: str):
    return getattr(_current, name)
