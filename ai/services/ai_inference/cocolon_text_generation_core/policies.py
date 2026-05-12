# -*- coding: utf-8 -*-
from __future__ import annotations

"""Policy constants for the Cocolon text generation core.

This module intentionally keeps policy names internal and additive.  It does
not change public API routes, database names, response keys, or visible labels.
"""

from typing import Iterable, Tuple

DEFAULT_COMPOSER_MODEL = "cocolon_text_generation_core.v0"

# Phase 8 is an explicit stop point: EmlisAI is fixed as the first connected
# user of the common core, but Piece / Analysis text generation are not wired
# yet. These tokens are internal meta labels only; they do not rename routes,
# DB objects, response keys, or visible labels.
TEXT_GENERATION_CORE_PHASE8_STOP_POINT = "emlis_regression_fixed_before_piece_analysis"
TEXT_GENERATION_CORE_PHASE8_NEXT_PHASE = "piece_composer_input_contract_design"

CORE_ID_EMLIS = "emlis"
CORE_ID_PIECE = "piece"
CORE_ID_ANALYSIS = "analysis"
KNOWN_CORE_IDS: Tuple[str, ...] = (CORE_ID_EMLIS, CORE_ID_PIECE, CORE_ID_ANALYSIS)

STATUS_GENERATED = "generated"
STATUS_PASSED = "passed"
STATUS_REJECTED = "rejected"
STATUS_UNAVAILABLE = "unavailable"

PASSING_STATUSES: Tuple[str, ...] = (STATUS_GENERATED, STATUS_PASSED)
FAILING_STATUSES: Tuple[str, ...] = (STATUS_REJECTED, STATUS_UNAVAILABLE)
KNOWN_STATUSES: Tuple[str, ...] = PASSING_STATUSES + FAILING_STATUSES

DEFAULT_COVERAGE_SCOPE = "partial_observation"
FAIL_CLOSED_COVERAGE_SCOPE = "unavailable"

QUALITY_FLAG_PAYLOAD_INVALID = "payload_invalid"
QUALITY_FLAG_EVIDENCE_MISSING = "evidence_missing"
QUALITY_FLAG_PHRASE_UNIT_MISSING = "phrase_unit_missing"
QUALITY_FLAG_SENTENCE_PLAN_MISSING = "sentence_plan_missing"

REJECTION_CORE_ID_MISSING = "core_id_missing"
REJECTION_EVIDENCE_MISSING = "source_evidence_missing"
REJECTION_PHRASE_UNIT_MISSING = "phrase_unit_missing"
REJECTION_SENTENCE_PLAN_MISSING = "sentence_plan_missing"
REJECTION_MUST_KEEP_ROLE_MISSING = "must_keep_role_missing"
REJECTION_RESULT_TEXT_MISSING = "result_text_missing"
REJECTION_RESULT_EVIDENCE_MISSING = "result_used_evidence_missing"


def clean_token(value: object) -> str:
    """Return a stripped internal token without guessing a replacement."""

    return str(value or "").strip()


def compact_tokens(values: Iterable[object] | None) -> Tuple[str, ...]:
    """Normalize a sequence into unique non-empty string tokens."""

    out: list[str] = []
    for value in values or ():
        item = clean_token(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def normalize_status(value: object) -> str:
    status = clean_token(value)
    if status in KNOWN_STATUSES:
        return status
    return STATUS_UNAVAILABLE
