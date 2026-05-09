# -*- coding: utf-8 -*-
from __future__ import annotations

"""Perspective board for EmlisAI specialist observer reports."""

from typing import Sequence

from emlis_ai_types import EvidenceSpan, PerspectiveBoard, PerspectiveReport


def build_perspective_board(*, evidence_spans: Sequence[EvidenceSpan], reports: Sequence[PerspectiveReport]) -> PerspectiveBoard:
    return PerspectiveBoard(
        evidence_spans=list(evidence_spans or []),
        reports=list(reports or []),
    )


__all__ = ["build_perspective_board"]
