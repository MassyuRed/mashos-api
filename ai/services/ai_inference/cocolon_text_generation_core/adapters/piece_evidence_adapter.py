# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 3 skeleton for future Piece evidence adaptation."""

from typing import Any, Iterable

from cocolon_text_generation_core.evidence import EvidenceConversionResult, empty_evidence_adapter_result
from cocolon_text_generation_core.policies import CORE_ID_PIECE

ADAPTER_NAME = "piece_evidence_adapter.skeleton.v0"
REJECTION_NOT_CONNECTED = "piece_evidence_adapter_not_connected"


def convert_piece_evidence_spans(_items: Iterable[Any] | None = None, **_kwargs: Any) -> EvidenceConversionResult:
    """Return fail-closed skeleton until PieceComposer phases connect evidence."""

    return empty_evidence_adapter_result(
        core_id=CORE_ID_PIECE,
        adapter_name=ADAPTER_NAME,
        reason=REJECTION_NOT_CONNECTED,
        meta={"source_core": CORE_ID_PIECE, "phase": "phase3_skeleton_only"},
    )


def adapt_piece_evidence_sources(*args: Any, **kwargs: Any) -> EvidenceConversionResult:
    """Alias for the later Composer-facing naming style."""

    return convert_piece_evidence_spans(*args, **kwargs)


__all__ = ["ADAPTER_NAME", "REJECTION_NOT_CONNECTED", "adapt_piece_evidence_sources", "convert_piece_evidence_spans"]
