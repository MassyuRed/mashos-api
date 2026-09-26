"""Disabled B8 entry and original-snapshot grammar admission.

CMEE owns Piece source meaning, intent, ArtifactPlan and canonical text.
This module retains the existing caller shape; it does not retrieve saved inputs,
authenticate callers, create records, consume quota or enable a public route.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from piece_v2_content_policy import unavailable
from cocolon_meaning_experience_engine.piece_source import _PLAIN_EVALUATION_MODAL


@dataclass(frozen=True, repr=False)
class PieceSourceSnapshot:
    owner_id: str
    saved_input_id: str
    source_version: str
    original_text: str
    source_role: str = 'original'
    source_stage: str = 'normal_observation'
    # Optional complete saved-record projection, never a public payload. The
    # source builder verifies original_text against both written fields and
    # binds all metadata to the same immutable record before generation.
    saved_original_json: bytes | None = None


# This is a grammar operation, not a table of input sentences or generated
# closures. Only these unambiguously transitive predicates admit を insertion.
# Past copulas and quoted/nested focal clauses are deliberately not admitted.
_PREDICATES = ('大切にしたい', '大切にしている', '大切にしたくない',
               '望んでいる', '望んでいない', '選びたい', '選びたくない')


def _transitive_predicate_forms() -> tuple[tuple[str, ...], tuple[str, ...], frozenset[str]]:
    """Share finite forms of the existing predicates, not a new lexicon.

    The third set contains only plain bases licensed before a finite
    modal. A past member of that set can also modify the focal nominal;
    polite finite predicates cannot. All writers retain source wording.
    """
    predicates = list(_PREDICATES)
    past_predicates = []
    modal_predicates = set(_PREDICATES)
    for predicate in _PREDICATES:
        if predicate.endswith(('たい', 'たくない')):
            predicates.append(predicate + 'です')
            past = predicate[:-1] + 'かった'
            past_predicates.extend((past, past + 'です'))
            modal_predicates.add(past)
        elif predicate.endswith('いない'):
            stem = predicate[:-len('いない')]
            predicates.append(stem + 'いません')
            past_predicates.extend((stem + 'いなかった', stem + 'いませんでした'))
            modal_predicates.add(stem + 'いなかった')
        elif predicate.endswith('いる'):
            stem = predicate[:-len('いる')]
            predicates.append(stem + 'います')
            past_predicates.extend((stem + 'いた', stem + 'いました'))
            modal_predicates.add(stem + 'いた')
    return tuple(predicates), tuple(past_predicates), frozenset(modal_predicates)

# Bind the already-supported first-person spellings as source material. The
# writer and reference-linked continuity must use this same captured author.
# Past belongs to the embedded predicate, not the final copula or a word
# inside its object. Reuse the direct construction's plain past forms; neither
# polite relative predicates nor stacked modals gain admission here.
# The existing plain modal owner qualifies the WHOLE predicate, just as in
# the direct word order. Keep its literal wording inside the predicate span
# for the unchanged author and uncertainty/format checks; never infer a vow.
_FINITE_PREDICATES, _PAST_PREDICATES, _PLAIN_PREDICATES = _transitive_predicate_forms()
_FOCUS = re.compile(r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)が(?P<predicate>(?:(?:'
                    + '|'.join(map(re.escape, _PREDICATES)) + r')|(?P<past_predicate>'
                    + '|'.join(re.escape(p) for p in _PAST_PREDICATES if p in _PLAIN_PREDICATES)
                    + r'))(?P<modal>' + _PLAIN_EVALUATION_MODAL
                    + r')?)のは[、，,]?(?P<object>.+?)(?:です|だ)[。]$')
_UNCERTAIN = re.compile(r'かもしれ|分から|わから|迷って|迷い|まだ決め|とは限ら|たぶん|おそらく')
_DEICTIC = re.compile(r'^(?:これ|それ|あれ|ここ|そこ|あそこ)(?:は|が|を|に|で|も)')
_NESTED = re.compile(r'[「」『』"“”]|(?:[がは]私)|(?:と(?:彼|彼女|上司|友人))')


def _sentences(text: str) -> list[str]:
    # No sentence splitting inside quotes is attempted by this first vertical.
    if any(c in text for c in '「」『』"“”'):
        raise unavailable('quoted_discourse_not_yet_supported')
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    nonempty = [line.strip() for line in lines if line.strip()]
    if any(line[-1] not in '。！？!?' for line in nonempty):
        raise unavailable('source_line_mid_sentence')
    joined = ''.join(nonempty)
    pieces = re.findall(r'[^。！？!?]+[。！？!?]', joined)
    if not pieces or ''.join(pieces) != joined or len(pieces) > 6:
        raise unavailable('complete_sentence_required')
    # Horizontal separators belong to the gap between sentences, not to the
    # next sentence's speaker or reference. Keep sentence-internal whitespace
    # and punctuation verbatim; never normalize the original source. CMEE
    # locates these exact substrings in the raw text, preserving scalar/UTF-8
    # evidence coordinates and the original newline barriers for the writer.
    pieces = [piece.lstrip(' \t\u3000') for piece in pieces]
    if any(len(piece) == 1 for piece in pieces):
        raise unavailable('complete_sentence_required')
    return pieces


def generate_piece_candidate(source: PieceSourceSnapshot, *, authenticated_owner_id: str,
                             tier: str = 'free', requested_format: str | None = None) -> dict:
    """Existing disabled B8 entry, now consuming CMEE's Piece artifact directly.

    Owner equality is a binding check, NOT authentication. B5 must still obtain
    the immutable saved source; no API, DB, quota or native route is enabled.
    """
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest, PieceEngineOutcome
    from cocolon_meaning_experience_engine.contracts import EngineStatus
    if type(source) is not PieceSourceSnapshot:
        raise unavailable('source_type')
    request = PieceGenerationRequest(
        request_id='piece-offline-candidate', source=source,
        expected_owner_id=authenticated_owner_id,
        expected_saved_input_id=source.saved_input_id,
        expected_source_version=source.source_version,
        tier=tier, requested_format=requested_format)
    outcome = MeaningExperienceEngine().generate(request)
    if not isinstance(outcome, PieceEngineOutcome):
        raise unavailable('piece_engine_outcome_type')
    if (outcome.status != EngineStatus.GENERATED or outcome.artifact is None
            or outcome.artifact_plan is None or outcome.source_meaning is None):
        raise unavailable(outcome.reason_codes[0] if outcome.reason_codes else 'piece_content_unavailable')
    return outcome.artifact.as_candidate()
