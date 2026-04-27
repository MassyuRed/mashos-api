# -*- coding: utf-8 -*-
"""Legacy MyModel resonances ranking compat facade.

The current owner is ``api_ranking_piece_resonances``. This module is kept only
for legacy imports during the rename-safe phase.
"""

from __future__ import annotations

from api_ranking_piece_resonances import (
    _build_ranking_piece_resonances_payload,
    _coerce_int,
    _coerce_text,
    _fetch_ready_board_rows,
    _pick_resonance_count,
    _publish_resonance_items,
    logger,
    register_ranking_piece_resonances_routes,
)


def register_ranking_mymodel_resonances_routes(app):
    """Delegate legacy registration to the current Piece ranking owner."""
    register_ranking_piece_resonances_routes(app)


__all__ = [
    "_build_ranking_piece_resonances_payload",
    "_coerce_int",
    "_coerce_text",
    "_fetch_ready_board_rows",
    "_pick_resonance_count",
    "_publish_resonance_items",
    "register_ranking_mymodel_resonances_routes",
]
