# -*- coding: utf-8 -*-
"""Compatibility-only Nexus routes retired from the canonical public surface."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException


def register_nexus_compat_routes(app: FastAPI) -> None:
    @app.get("/nexus/history/discoveries")
    async def nexus_history_discoveries_compat() -> Any:
        raise HTTPException(status_code=410, detail="Discoveries is no longer available")
