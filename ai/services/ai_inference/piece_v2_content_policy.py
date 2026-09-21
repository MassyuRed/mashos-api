"""B8 candidate policy. Pure, offline-only; not source retrieval or a public gate.

The bounded editorial compiler has no permission to infer missing meaning.
Original and supplemental admission/CMEE integration remain separate work.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from piece_v2_contract import PieceContractError, reconstruct_piece_text
from piece_text_formatter import format_reflection_text

FORMATS = ('short_essay', 'quote', 'declaration')
ENVELOPES = {'short_essay': (24, 420, 6), 'quote': (12, 120, 2),
             'declaration': (12, 180, 4)}


def unavailable(code: str) -> PieceContractError:
    return PieceContractError('PIECE_CONTENT_UNAVAILABLE', code)


def validate_candidate_text(payload: Mapping) -> str:
    """Validate canonical shape/envelope, not semantic or public acceptance."""
    text = reconstruct_piece_text(payload)
    lo, hi, sentences = ENVELOPES[payload['format_type']]
    n = len(re.sub(r'\s', '', text))
    if not lo <= n <= hi or len(re.findall(r'[。！？!?]', text)) > sentences:
        raise unavailable('content_envelope')
    if any('\n' in b for b in payload['body_blocks']):
        raise unavailable('embedded_block_break')
    return text


def check_existing_detectors(text: str) -> None:
    """Reuse existing detectors; refusal is NOT a complete public safety proof.

    No masked-token or generic fallback is emitted. In particular the legacy
    normalizer's zero-width removal must not split a ZWJ emoji in Piece.
    """
    if any(0xD800 <= ord(c) <= 0xDFFF for c in text):
        raise unavailable('malformed_unicode')
    if any(ord(c) in {*range(0x202A, 0x202F), *range(0x2066, 0x206A),
                     0x200B, 0xFEFF} for c in text):
        raise unavailable('hidden_control')
    result = format_reflection_text(text)
    # ASCII mail addresses can touch Japanese words on both sides; Unicode
    # word-boundary checks in the legacy detector do not cover that form.
    adjacent_mail = re.search(r'(?i)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', text)
    if result.flags or result.display_text is None or adjacent_mail:
        raise unavailable('existing_safety_detector')
    if re.search(r'(?i)(?:bearer\s+|(?:api[_ -]?key|password|token)\s*[:=]|postgres(?:ql)?://)', text):
        raise unavailable('credential_like_material')


def choose_format(*, tier: str, requested: str | None, eligible: tuple[str, ...],
                  recommended: str) -> str:
    if tier not in ('free', 'plus', 'premium'):
        raise unavailable('tier_invalid')
    if requested is not None and (tier != 'premium' or requested not in eligible):
        raise unavailable('format_choice_not_admitted')
    selected = requested or ('short_essay' if tier == 'free' else recommended)
    if selected not in eligible:
        raise unavailable('format_not_eligible')
    return selected
