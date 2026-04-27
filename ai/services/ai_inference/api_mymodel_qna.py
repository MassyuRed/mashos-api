# -*- coding: utf-8 -*-
"""Legacy MyModel QnA compat facade.

The current owner is ``api_piece_runtime``. This module forwards legacy imports
while physical DB/table names remain MyModel/QnA-compatible until the DB rename
phase.
"""

from __future__ import annotations

import sys
import types

import api_piece_runtime as _current

QnaListResponse = _current.QnaListResponse
QnaDetailResponse = _current.QnaDetailResponse
QnaViewResponse = _current.QnaViewResponse
QnaResonanceResponse = _current.QnaResonanceResponse
QnaEchoesSubmitResponse = _current.QnaEchoesSubmitResponse
QnaEchoesDeleteResponse = _current.QnaEchoesDeleteResponse
QnaEchoesHistoryResponse = _current.QnaEchoesHistoryResponse
QnaSavedReflectionsResponse = _current.QnaSavedReflectionsResponse
QnaUnreadResponse = _current.QnaUnreadResponse
QnaUnreadStatusResponse = _current.QnaUnreadStatusResponse
QnaRecommendUsersResponse = _current.QnaRecommendUsersResponse
QnaViewRequest = _current.QnaViewRequest
QnaResonanceRequest = _current.QnaResonanceRequest
QnaEchoesSubmitRequest = _current.QnaEchoesSubmitRequest
QnaEchoesDeleteRequest = _current.QnaEchoesDeleteRequest
PieceLibraryResponse = _current.PieceLibraryResponse
PieceDetailResponse = _current.PieceDetailResponse
PieceViewResponse = _current.PieceViewResponse
PieceResonanceResponse = _current.PieceResonanceResponse
PieceResonanceSubmitResponse = _current.PieceResonanceSubmitResponse
PieceResonanceDeleteResponse = _current.PieceResonanceDeleteResponse
PieceResonanceHistoryResponse = _current.PieceResonanceHistoryResponse
PieceResonancePiecesResponse = _current.PieceResonancePiecesResponse
PieceUnreadResponse = _current.PieceUnreadResponse
PieceUnreadStatusResponse = _current.PieceUnreadStatusResponse
PieceRecommendUsersResponse = _current.PieceRecommendUsersResponse
PieceViewRequest = _current.PieceViewRequest
PieceResonanceRequest = _current.PieceResonanceRequest
PieceResonanceSubmitRequest = _current.PieceResonanceSubmitRequest
PieceResonanceDeleteRequest = _current.PieceResonanceDeleteRequest


def register_mymodel_qna_routes(app):
    return _current.register_mymodel_qna_routes(app)


def register_piece_runtime_routes(app):
    return _current.register_piece_runtime_routes(app)


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


__all__ = [
    "QnaListResponse",
    "QnaDetailResponse",
    "QnaViewResponse",
    "QnaResonanceResponse",
    "QnaEchoesSubmitResponse",
    "QnaEchoesDeleteResponse",
    "QnaEchoesHistoryResponse",
    "QnaSavedReflectionsResponse",
    "QnaUnreadResponse",
    "QnaUnreadStatusResponse",
    "QnaRecommendUsersResponse",
    "QnaViewRequest",
    "QnaResonanceRequest",
    "QnaEchoesSubmitRequest",
    "QnaEchoesDeleteRequest",
    "PieceLibraryResponse",
    "PieceDetailResponse",
    "PieceViewResponse",
    "PieceResonanceResponse",
    "PieceResonanceSubmitResponse",
    "PieceResonanceDeleteResponse",
    "PieceResonanceHistoryResponse",
    "PieceResonancePiecesResponse",
    "PieceUnreadResponse",
    "PieceUnreadStatusResponse",
    "PieceRecommendUsersResponse",
    "PieceViewRequest",
    "PieceResonanceRequest",
    "PieceResonanceSubmitRequest",
    "PieceResonanceDeleteRequest",
    "register_mymodel_qna_routes",
    "register_piece_runtime_routes",
]
