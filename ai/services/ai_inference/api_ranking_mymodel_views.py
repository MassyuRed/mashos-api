# -*- coding: utf-8 -*-
"""Legacy MyModel views ranking compat facade.

The current owner is ``api_ranking_piece_views``. This module is kept only for
legacy imports during the rename-safe phase.
"""

from __future__ import annotations

from api_ranking_piece_views import (
    _build_ranking_piece_views_payload,
    _coerce_int,
    _coerce_text,
    _fetch_ready_board_rows,
    _pick_view_count,
    _publish_view_items,
    logger,
    register_ranking_piece_views_routes,
)


def register_ranking_mymodel_views_routes(app):
    """Delegate legacy registration to the current Piece ranking owner."""
    register_ranking_piece_views_routes(app)


__all__ = [
    "_build_ranking_piece_views_payload",
    "_coerce_int",
    "_coerce_text",
    "_fetch_ready_board_rows",
    "_pick_view_count",
    "_publish_view_items",
    "register_ranking_mymodel_views_routes",
]
