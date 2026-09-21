"""B8 bounded first-person editorial compiler; disabled candidate entry only.

This is NOT the CMEE Piece consumer or an authenticated preview API. It accepts
an internal saved-source snapshot supplied by a trusted caller. It currently
handles explicit first-person focal constructions, plus their complete adjacent
sentences. Unsupported discourse is unavailable, never raw-source fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from piece_v2_content_policy import (check_existing_detectors, choose_format,
                                     unavailable, validate_candidate_text)


@dataclass(frozen=True)
class PieceSourceSnapshot:
    owner_id: str
    saved_input_id: str
    source_version: str
    original_text: str
    source_role: str = 'original'
    source_stage: str = 'normal_observation'


# This is a grammar operation, not a table of input sentences or generated
# closures. Only these unambiguously transitive predicates admit を insertion.
# Past copulas and quoted/nested focal clauses are deliberately not admitted.
_PREDICATES = ('大切にしたい', '大切にしている', '大切にしたくない',
               '望んでいる', '望んでいない', '選びたい', '選びたくない')
_FOCUS = re.compile(r'^私が(?P<predicate>' + '|'.join(_PREDICATES) +
                    r')のは[、，,]?(?P<object>.+?)(?:です|だ)[。]$')
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
    return pieces


def generate_piece_candidate(source: PieceSourceSnapshot, *, authenticated_owner_id: str,
                             tier: str = 'free', requested_format: str | None = None) -> dict:
    """Return actual candidate text with no writes, quota or runtime activation.

    Equality of owner IDs is a binding check, NOT authentication. The caller is
    responsible for authentication and immutable saved-source retrieval (B5).
    """
    if type(source) is not PieceSourceSnapshot:
        raise unavailable('source_type')
    if not all(isinstance(x, str) and x for x in
               (source.owner_id, source.saved_input_id, source.source_version,
                source.original_text, authenticated_owner_id)):
        raise unavailable('source_identity')
    if source.owner_id != authenticated_owner_id:
        raise unavailable('source_owner_mismatch')
    if source.source_role != 'original' or source.source_stage not in (
            'normal_observation', 'pre_question_observation'):
        raise unavailable('source_role_or_stage_not_yet_supported')
    check_existing_detectors(source.original_text)
    sentences = _sentences(source.original_text)
    edited: list[str] = []
    focal_count = 0
    for sentence in sentences:
        m = _FOCUS.fullmatch(sentence)
        if m:
            obj = m['object'].lstrip('、，,')
            if (not obj or not obj.endswith(('こと', 'もの', '時間'))
                    or _NESTED.search(obj) or _DEICTIC.search(obj)):
                raise unavailable('focal_object_not_self_contained')
            # All object text, including internal contrast, negation and time,
            # remains verbatim. The existing predicate is moved, not inferred.
            edited.append('私は、' + obj + 'を' + m['predicate'] + '。')
            focal_count += 1
        else:
            edited.append(sentence)
    if not focal_count:
        raise unavailable('expression_not_yet_supported')
    if any(_DEICTIC.search(s) for s in sentences):
        raise unavailable('unresolved_reference')
    # Preserve source order. No deduplication (which could erase emphasis),
    # invented connection, past/current merge, or hidden title is allowed.
    # At most three meaning blocks; adjacent complete clauses stay in order.
    if len(edited) <= 3:
        blocks = edited
    else:
        blocks = [edited[0], ''.join(edited[1:-1]), edited[-1]]
    eligible: list[str] = []
    payloads: dict[str, dict] = {}
    for fmt in ('short_essay', 'quote', 'declaration'):
        if fmt == 'quote' and len(edited) != 1:
            continue
        # Intent must be explicit in the transformed source, with no uncertain
        # adjacent discourse. Multiple stances are not collapsed to a promise.
        if fmt == 'declaration' and (len(edited) != 1 or _UNCERTAIN.search(edited[0])):
            continue
        payload = {'schema_version': 'piece.content_payload.v1', 'format_type': fmt,
                   'body_blocks': blocks[:], 'title': None, 'language': 'ja',
                   'meaning_contract_version': 'piece.content_meaning.v1',
                   'safety_contract_version': 'piece.public_safety_transformation.v1'}
        try:
            validate_candidate_text(payload)
        except ValueError:
            continue
        eligible.append(fmt)
        payloads[fmt] = payload
    preferred = 'declaration' if 'declaration' in eligible else (
        'quote' if 'quote' in eligible else 'short_essay')
    selected = choose_format(tier=tier, requested=requested_format,
                             eligible=tuple(eligible), recommended=preferred)
    payload = payloads[selected]
    text = validate_candidate_text(payload)
    check_existing_detectors(text)
    return {'candidate_state': 'OFFLINE_NOT_ACCEPTED', 'content_payload': payload,
            'piece_text': text, 'piece_text_hash': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'eligible_formats': eligible, 'format_type': selected,
            'production_enabled': False, 'record_effect': 0, 'quota_effect': 0}
