"""Piece-owned paragraph intent over the existing shared InputMeaningBlock.

This is a bounded, code-disabled editorial consumer, not CMEE's complete
SourceBoundMeaningGraph/ArtifactPlan consumer. It makes an independent final
self-owned wish the reading entry, while keeping every context sentence.
The shared service's summaries, heuristic tension pairs and coverage/dedup
choices are never used as canonical Piece words or inferred relations.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Sequence

from emlis_ai_input_meaning_block_service import build_input_meaning_blocks
from emlis_ai_types import EvidenceRef
from piece_v2_content_policy import unavailable

_SELF_TOPIC = re.compile(r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)は[、，,]?(?P<body>.+)。$')
# Grammatical wish endings, not topic vocabulary or completed output templates.
_WISH_END = re.compile(r'(?:[てで]みたい|(?<!み)たい|たくない)(?:です)?$')
_DEPENDENT_START = re.compile(
    r'^(?:だから|そのため|その結果|それでも|それから|それに|それなら|つまり|でも|だけど|'
    r'けれど|しかし|ただし|ただ[、，,]|一方|とはいえ|そして|すると|なぜなら)')
_REFERENCE = re.compile(r'(?:これ|それ|あれ|ここ|そこ|あそこ)(?:は|が|を|に|で|も|の|と|から)|(?:この|その|あの)')
_EMBEDDED_REPORT = re.compile(r'(?:たい|たくない)(?:と|って)(?:言|いわ|話|語|伝え|聞|書)')
# The shared compatibility classifier may label an entire conditional wish
# as a constraint. Its label is not promoted into a new intention or claim.
_INTENT_ROLES = frozenset({'self_view', 'wish_or_hope', 'continuation_wish',
                           'not_want_to_quit', 'dual_holding', 'limit_or_exhaustion'})


@dataclass(frozen=True, repr=False)
class PieceExpressionPlan:
    """Request-local text plan, not a new public/schema or persistence owner."""
    source_sentence_order: tuple[int, ...]
    sentences: tuple[str, ...]
    body_blocks: tuple[str, ...]


def compile_piece_expression_plan(*, sentences: Sequence[str],
                                  evidence: EvidenceRef) -> PieceExpressionPlan:
    """Express one independent final wish before its intact preceding context.

    No zero-subject resolution, causal inference, reported speech, anaphora
    repair, semantic compression or source-only fallback is claimed here.
    Complete dependent clauses inside a sentence stay attached to that sentence.
    The original final position is required so following qualifications cannot
    accidentally be separated from a selected wish.
    """
    original = tuple(sentences)
    if not 2 <= len(original) <= 6 or any(not s.endswith('。') for s in original):
        raise unavailable('expression_not_yet_supported')
    topic = _SELF_TOPIC.fullmatch(original[-1])
    if topic is None or not _WISH_END.search(topic['body']):
        raise unavailable('expression_not_yet_supported')
    # A discourse link cannot be detached merely because its sentence can be
    # copied. Keep this bounded reordering unavailable rather than drop links.
    if any(_DEPENDENT_START.search(s) or _REFERENCE.search(s) for s in original):
        raise unavailable('expression_requires_source_order')
    if _DEPENDENT_START.search(topic['body']) or _EMBEDDED_REPORT.search(topic['body']):
        raise unavailable('expression_requires_source_order')
    blocks = build_input_meaning_blocks(current_input={'memo': ''.join(original)},
                                       shaped_user_phrases=(), evidence=evidence)
    final_key = f'meaning:{len(original) - 1}:'
    focus = [b for b in blocks if b.block_key.startswith(final_key)]
    if (len(focus) != 1 or focus[0].role not in _INTENT_ROLES
            or not focus[0].include_in_piece_core):
        raise unavailable('expression_meaning_not_admitted')
    # Bind the shared source-order block, but never realize its shortened
    # summary or its label. Duplicate context remains in `original`, not in
    # the shared service's deduplicated block list.
    ordered = (topic['speaker'] + 'は、' + topic['body'] + '。', *original[:-1])
    return PieceExpressionPlan(
        source_sentence_order=(len(original) - 1, *range(len(original) - 1)),
        sentences=ordered, body_blocks=(ordered[0], ''.join(ordered[1:])),
    )
