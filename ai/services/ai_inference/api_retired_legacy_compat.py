from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException


def _gone(detail: str) -> HTTPException:
    return HTTPException(status_code=410, detail=detail)


def register_retired_legacy_compat_routes(app: FastAPI) -> None:
    """Register unpaired legacy public endpoints that are intentionally retired.

    These endpoints have no canonical replacement and must not live in core runtime modules.
    They remain available only as 410 compatibility surfaces during the sunset window.
    """

    @app.get("/friends/manage")
    async def friends_manage_retired() -> Any:
        raise _gone("Friends manage is no longer available")

    @app.get("/mymodel/qna/discoveries/reflections")
    async def piece_discoveries_reflections_retired() -> Any:
        raise _gone("Discoveries is no longer available")

    @app.post("/mymodel/qna/discoveries/submit")
    async def piece_discoveries_submit_retired() -> Any:
        raise _gone("Discoveries is no longer available")

    @app.post("/mymodel/qna/discoveries/delete")
    async def piece_discoveries_delete_retired() -> Any:
        raise _gone("Discoveries is no longer available")

    @app.get("/mymodel/qna/discoveries/history")
    async def piece_discoveries_history_retired() -> Any:
        raise _gone("Discoveries is no longer available")

    @app.get("/ranking/mymodel_questions")
    async def ranking_piece_questions_retired() -> Any:
        raise _gone("Piece question ranking is no longer available")

    @app.get("/ranking/mymodel_discoveries")
    async def ranking_piece_discoveries_retired() -> Any:
        raise _gone("Piece discoveries ranking is no longer available")
