# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 3 skeleton for future Analysis evidence adaptation."""

from typing import Any, Iterable

from cocolon_text_generation_core.evidence import EvidenceConversionResult, empty_evidence_adapter_result
from cocolon_text_generation_core.policies import CORE_ID_ANALYSIS

ADAPTER_NAME = "analysis_evidence_adapter.skeleton.v0"
REJECTION_NOT_CONNECTED = "analysis_evidence_adapter_not_connected"


def convert_analysis_evidence_spans(_items: Iterable[Any] | None = None, **_kwargs: Any) -> EvidenceConversionResult:
    """Return fail-closed skeleton until AnalysisComposer phases connect evidence."""

    return empty_evidence_adapter_result(
        core_id=CORE_ID_ANALYSIS,
        adapter_name=ADAPTER_NAME,
        reason=REJECTION_NOT_CONNECTED,
        meta={"source_core": CORE_ID_ANALYSIS, "phase": "phase3_skeleton_only"},
    )


def adapt_analysis_evidence_sources(*args: Any, **kwargs: Any) -> EvidenceConversionResult:
    """Alias for the later Composer-facing naming style."""

    return convert_analysis_evidence_spans(*args, **kwargs)


__all__ = ["ADAPTER_NAME", "REJECTION_NOT_CONNECTED", "adapt_analysis_evidence_sources", "convert_analysis_evidence_spans"]
