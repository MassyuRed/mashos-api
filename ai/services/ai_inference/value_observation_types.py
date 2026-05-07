# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared value-observation types for Cocolon's three core structures.

These types describe source-grounded observation signals that can be reused by
EmlisAI, Piece, and Analysis without coupling those pipelines together.  They
are not fixed reply templates; they are structured hints about what the current
input appears to contain.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

VALUE_OBSERVATION_SCHEMA_VERSION = "cocolon.value_observation.v1"


@dataclass(frozen=True)
class ValueObservationSignal:
    signal_key: str
    title: str
    observation_axis: str
    surface_text: str
    latent_structure: str
    value_conversion: str
    evidence_terms: List[str] = field(default_factory=list)
    source_fields: List[str] = field(default_factory=list)
    target_cores: List[str] = field(default_factory=list)
    confidence: float = 0.0
    public_safe: bool = True
    softening_required: bool = False
    no_diagnosis: bool = True
    no_personality_claim: bool = True
    emlis_text: str = ""
    piece_question: str = ""
    piece_answer: str = ""
    analysis_hint: str = ""
    must_keep_terms: List[str] = field(default_factory=list)
    priority: int = 0
    schema_version: str = VALUE_OBSERVATION_SCHEMA_VERSION

    def as_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "signal_key": self.signal_key,
            "title": self.title,
            "observation_axis": self.observation_axis,
            "surface_text": self.surface_text,
            "latent_structure": self.latent_structure,
            "value_conversion": self.value_conversion,
            "evidence_terms": list(self.evidence_terms),
            "source_fields": list(self.source_fields),
            "target_cores": list(self.target_cores),
            "confidence": float(self.confidence),
            "public_safe": bool(self.public_safe),
            "softening_required": bool(self.softening_required),
            "no_diagnosis": bool(self.no_diagnosis),
            "no_personality_claim": bool(self.no_personality_claim),
            "must_keep_terms": list(self.must_keep_terms),
            "priority": int(self.priority),
        }


@dataclass(frozen=True)
class ValueObservationPlan:
    input_level: str
    signal_count: int
    primary_signal_keys: List[str] = field(default_factory=list)
    must_keep_signal_keys: List[str] = field(default_factory=list)
    optional_signal_keys: List[str] = field(default_factory=list)
    overcompression_risk: bool = False
    grounding_terms: List[str] = field(default_factory=list)
    schema_version: str = VALUE_OBSERVATION_SCHEMA_VERSION

    def as_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "input_level": self.input_level,
            "signal_count": int(self.signal_count),
            "primary_signal_keys": list(self.primary_signal_keys),
            "must_keep_signal_keys": list(self.must_keep_signal_keys),
            "optional_signal_keys": list(self.optional_signal_keys),
            "overcompression_risk": bool(self.overcompression_risk),
            "grounding_terms": list(self.grounding_terms),
        }


__all__ = [
    "VALUE_OBSERVATION_SCHEMA_VERSION",
    "ValueObservationPlan",
    "ValueObservationSignal",
]
