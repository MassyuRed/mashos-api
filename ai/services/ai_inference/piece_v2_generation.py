"""Disabled B8 entry and original-snapshot grammar admission.

CMEE owns Piece source meaning, intent, ArtifactPlan and canonical text.
This module retains the existing caller shape; it does not retrieve saved inputs,
authenticate callers, create records, consume quota or enable a public route.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from piece_v2_content_policy import unavailable, validate_source_meaning_preservation
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
# The negative ongoing state is the same source-written valuing predicate,
# not the distinct wish 大切にしたくない. Existing finite inflection, source
# binding and authorship preserve its negation/time; no intent is inferred.
_PREDICATES = ('大切にしたい', '大切にしている', '大切にしていない', '大切にしたくない',
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
# One written comma after the explicit author's が is a clause pause,
# not part of the predicate or an inferred subject. Keep capture spans
# in the untouched source for the existing resolver and writer. Multiple
# separators, whitespace and missing/other authors gain no admission.
# After のは and its optional comma, a horizontal pause is a separator,
# not part of the object. The new gap arm cannot stop inside whitespace or
# consume another comma; the existing no-gap parse remains available.
_FOCUS = re.compile(r'^(?P<speaker>私|わたし|僕|ぼく|俺|おれ)が[、，,]?(?P<predicate>(?:(?:'
                    + '|'.join(map(re.escape, _PREDICATES)) + r')|(?P<past_predicate>'
                    + '|'.join(re.escape(p) for p in _PAST_PREDICATES if p in _PLAIN_PREDICATES)
                    + r'))(?P<modal>' + _PLAIN_EVALUATION_MODAL
                    + r')?)のは[、，,]?(?:[ \t\u3000]+(?![ \t\u3000、，,]))?'
                    r'(?P<object>.+?)(?:です|だ)[。！!]$')
_UNCERTAIN = re.compile(r'かもしれ|分から|わから|迷って|迷い|まだ決め|とは限ら|たぶん|おそらく')
_DEICTIC = re.compile(r'^(?:これ|それ|あれ|ここ|そこ|あそこ)(?:は|が|を|に|で|も)')
_NESTED = re.compile(r'[「」『』"“”]|(?:[がは]私)|(?:と(?:彼|彼女|上司|友人))')


# A final polite past action needs a written object and a supported predicate.
# Keep the established verbal-noun form and admit these exact lexical stems
# with the same affirmative or negative ending. No generic kana stem rule.
_OMITTED_ACCOUNT_OBJECT = re.compile(r'[一-龥々ァ-ヴ][一-龥々ァ-ヴーぁ-ん]{0,24}\Z')
_OMITTED_ACCOUNT_PREDICATE = re.compile(r'[一-龥々]{2,}し(?:ませんでした|ました)')
_ACCOUNT_LEXICAL_STEMS = r'(?:送り|読み|開け|終え|(?P<guarded_stem>始め|受け取り|閉め))'
_OMITTED_LEXICAL_PREDICATE = re.compile(_ACCOUNT_LEXICAL_STEMS + r'(?:ませんでした|ました)')
# An explicit declarative stop can also delimit the already-written polite
# nonpast forms of these same stems. Omitted stops retain the past-only
# grammar above; no kana stem, lexical entry or inferred time is introduced.
_PUNCTUATED_NONPAST_ACCOUNT_PREDICATE = re.compile(r'[一-龥々]{2,}し(?:ません|ます)')
_PUNCTUATED_NONPAST_LEXICAL_PREDICATE = re.compile(_ACCOUNT_LEXICAL_STEMS + r'(?:ません|ます)')
# These source-written clause operators have no kana-following boundary in
# the new account arm. A missing pause cannot make an unsupported condition
# or report into an unqualified account. Ambiguous source strings stay out.
_EXPLICIT_ACCOUNT_SCOPE = re.compile(
    r'ならば?|たら|れば|[えけげせてねべめ]ば|'
    r'(?P<report>(?:と|って)(?:言|い[ういわえっ]))')


def _has_unread_explicit_account_scope(sentence: str) -> bool:
    # 迷って owns its internal って; it is not reported speech, even when
    # followed by いた/いった. Check only finite report operators outside
    # already-written uncertainty words, never every と/って in the text.
    markers = tuple(_UNCERTAIN.finditer(sentence))
    return any(not (scope['report'] is not None and any(
        marker.start() <= scope.start() < marker.end() for marker in markers))
        for scope in _EXPLICIT_ACCOUNT_SCOPE.finditer(sentence))


def _unproved_explicit_account_object(obj: str) -> bool:
    # The final と of the existing nominalizer こと is a word boundary,
    # not a stranded case particle. No actor/name or nominal-word list is used.
    return bool(re.search(r'(?:[はがもにへでを]|(?<!こ)と)[、，, \t\u3000]*\Z', obj))
# Only an explicit calendar word and particle can intervene between を and
# the finite lexical predicate. The original wording remains the KEEP node.
_OMITTED_LEXICAL_TIME = re.compile(
    r'(?:今日|昨日|一昨日|おととい|今朝|昨夜|先日)(?:は|に)[、，,]?[ \t\u3000]*')
# Keep the added action/time arm out of quantified questions and conditional
# prefixes, without reclassifying the previously supported sentence shapes.
_OMITTED_NEW_PREFIX_GUARD = re.compile(
    r'(?:何の|なにの)(?![一-龥々ァ-ヴぁ-ん]{1,16}も(?:ない|無い))|'
    r'いくつの|(?:何|なん)(?:件|枚|冊|通|個)の|'
    r'[えけげせてねべめ]ば(?=[、，,\s一-龥々ァ-ヴ])')
_OMITTED_LEXICAL_SCOPE = re.compile(
    r'(?:^|[、，,\s])(?:もし|仮に|たとえ)|'
    r'(?:ならば?|たら|れば)(?=[、，,\s一-龥々ァ-ヴ])|'
    r'場合(?:[、，,\s]|は|には|でも)|'
    r'(?:と|って)(?:言われ|言った|言って|言いました|聞いた|聞いて|聞きました|'
    r'伝えた|伝えて|伝えました|話した|話して|話しました|書いた|書いて|書きました)')
# Reject common written question cues even without a question mark. Read a
# complete cue, not the interior of ほとんどの or an indefinite construction
# such as どこにも / どうしても. For newly excluded particles, require an
# overt non-hiragana boundary after も; もらった / もぐった / もって must
# not masquerade as that particle. Ambiguous hiragana continuations retain
# refusal. The existing いつも exclusion is unchanged; 誰/だれ uses the same
# bounded も/でも boundary. None supplies a predicate or sentence ending.
_OMITTED_ACCOUNT_QUESTION = re.compile(
    r'何を|なにを|ど(?:れ|ちら|なた)(?!も|か|でも)|(?<!ほ)(?<!ほとん)どの|'
    r'どう(?:いう|やって(?!も(?=[^ぁ-ん]|\Z))|して(?!も(?=[^ぁ-ん]|\Z))|いった)|'
    r'どこ(?:で(?!も)|に(?!(?:も|でも)(?=[^ぁ-ん]|\Z))|の|へ|から|まで(?!も)|を|が|は|と)|'
    r'(?<![こそあど])いつ(?!も|か|でも|までも)|(?:なぜ|何故)(?!か)|'
    r'何時(?:に|の|まで(?!も)|から|頃|ごろ)|'
    r'(?:誰|だれ)(?:が|の|を|に|と|から|まで|へ|で)(?!(?:も|でも)(?=[^ぁ-ん]|\Z))')


def _is_unpunctuated_account(text: str, *, allow_nonpast: bool = False) -> bool:
    obj, particle, predicate = text.rpartition('を')
    # A horizontal pause after the written object particle does not change
    # the finite predicate. Inspect this view only: the source, KEEP writer
    # and evidence spans retain every separator. Do not cross a line break.
    predicate = predicate.lstrip(' \t\u3000')
    clause = text.lstrip()
    # A pause before を is outside the written nominal object. Keep the
    # exact object/source for every other guard and all evidence coordinates.
    object_end = obj.rstrip(' \t\u3000')
    # The same pause cannot hide the existing 何を / なにを question cue.
    question_clause = object_end + particle + predicate if object_end != obj else clause
    if (not particle or not _OMITTED_ACCOUNT_OBJECT.search(object_end[-25:])
            or clause.startswith('もし') or _OMITTED_ACCOUNT_QUESTION.search(question_clause)):
        return False
    if _OMITTED_ACCOUNT_PREDICATE.fullmatch(predicate):
        return True
    # In the new explicit nonpast arm, a trailing topic/subject particle
    # cannot serve as the missing を-object. Ambiguous nominal endings stay
    # unadmitted here; this is not a general noun/particle parser. The old
    # omitted-stop/past grammar is unchanged.
    unproved_nonpast_object = _unproved_explicit_account_object(obj)
    nonpast_suru = allow_nonpast and _PUNCTUATED_NONPAST_ACCOUNT_PREDICATE.fullmatch(predicate)
    if nonpast_suru:
        from piece_v2_expression import _DEPENDENT_START
        return not (unproved_nonpast_object
                    or _OMITTED_NEW_PREFIX_GUARD.search(obj)
                    or _DEPENDENT_START.search(clause) or _OMITTED_LEXICAL_SCOPE.search(clause)
                    or _has_unread_explicit_account_scope(clause))
    time = _OMITTED_LEXICAL_TIME.match(predicate)
    if time:
        predicate = predicate[time.end():]
    lexical = _OMITTED_LEXICAL_PREDICATE.fullmatch(predicate)
    nonpast = (_PUNCTUATED_NONPAST_LEXICAL_PREDICATE.fullmatch(predicate)
               if allow_nonpast else None)
    lexical = lexical or nonpast
    if lexical is None:
        return False
    if nonpast and (unproved_nonpast_object or _has_unread_explicit_account_scope(clause)):
        return False
    if (time or lexical['guarded_stem'] or nonpast) and _OMITTED_NEW_PREFIX_GUARD.search(obj):
        return False
    from piece_v2_expression import _DEPENDENT_START
    return not (_DEPENDENT_START.search(clause) or _OMITTED_LEXICAL_SCOPE.search(clause))


def _sentences(text: str, *, allow_unpunctuated_account: bool = False) -> list[str]:
    # Reuse the existing strict delimiter reader for one literal quotation.
    # Its quote-aware sentence spans keep internal stops inside the same
    # source proposition. This supplies no reported speaker or meaning;
    # quoted newlines, multiple quotes and nesting retain their refusal.
    quote_spans = ()
    if any(c in text for c in '「」『』"“”'):
        from emlis_ai_grounded_sentence_surface import _body_primary_quote_spans
        spans, balanced = _body_primary_quote_spans(text)
        if (not balanced or len(spans) != 1
                or text.count('「') != 1 or text.count('」') != 1
                or any(c in text for c in '『』"“”')):
            raise unavailable('quoted_discourse_not_yet_supported')
        quoted = text[slice(*spans[0])]
        quote_tail = re.split(r'[\r\n]', text[spans[0][1] + 1:], maxsplit=1)[0].rstrip()
        if (not quoted.strip() or re.search(r'[\r\n]', quoted)
                or not quote_tail or quote_tail[-1] not in '。！？!?'):
            raise unavailable('quoted_discourse_not_yet_supported')
        quote_spans = spans
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    nonempty = [line.strip() for line in lines if line.strip()]
    pieces = []
    for line in nonempty:
        if quote_spans and '「' in line:
            from emlis_ai_grounded_sentence_surface import _body_sentence_spans
            complete, cursor = [], 0
            for _, end in _body_sentence_spans(line):
                # The shared witness trims horizontal gaps. Retain them in
                # this coverage view just as the existing regex did; the
                # final lstrip below owns the sentence separator treatment.
                complete.append(line[cursor:end])
                cursor = end
            # Preserve the existing one-stop outer sentence grammar. Runs
            # inside the quotation are opaque literal source text, while an
            # outer run or unfinished outer clause gains no new admission.
            if any(not p.endswith(tuple('。！？!?')) or len(p) < 2
                   or p[-2] in '。！？!?' for p in complete):
                raise unavailable('complete_sentence_required')
        else:
            complete = re.findall(r'[^。！？!?]+[。！？!?]', line)
        if line[-1] not in '。！？!?':
            tail = re.split(r'[。！？!?]', line)[-1]
            if not allow_unpunctuated_account or not _is_unpunctuated_account(tail):
                raise unavailable('source_line_mid_sentence')
            complete.append(tail)
        if ''.join(complete) != line:
            raise unavailable('complete_sentence_required')
        pieces.extend(complete)
    if not pieces or len(pieces) > 6:
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
                             tier: str = 'free', requested_format: str | None = None,
                             model_candidate=None) -> dict:
    """Existing disabled B8 entry, now consuming CMEE's Piece artifact directly.

    Owner equality is a binding check, NOT authentication. B5 must still obtain
    the immutable saved source; no API, DB, quota or native route is enabled.
    """
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.piece_source import build_piece_source_meaning
    from cocolon_meaning_experience_engine.piece_v1c import (
        PieceGenerationRequest, PieceEngineOutcome, PieceArtifact,
        compile_piece_artifact_plan, realize_piece_artifact,
    )
    from cocolon_meaning_experience_engine.contracts import EngineStatus
    from cocolon_meaning_experience_engine.piece_refined import (
        PieceRefinedSourceSnapshot, build_refined_meaning, _plans,
        realize_refined_piece_artifact, validate_refined_preservation,
    )
    refined = type(source) is PieceRefinedSourceSnapshot
    if type(source) is not PieceSourceSnapshot and not refined:
        raise unavailable('source_type')
    original = source.original if refined else source
    if type(original) is not PieceSourceSnapshot:
        raise unavailable('source_type')
    request = PieceGenerationRequest(
        request_id='piece-offline-candidate', source=source,
        expected_owner_id=authenticated_owner_id,
        expected_saved_input_id=original.saved_input_id,
        expected_source_version=original.source_version,
        tier=tier, requested_format=requested_format)
    outcome = (MeaningExperienceEngine().generate(request, semantic_input=model_candidate)
               if model_candidate is not None else MeaningExperienceEngine().generate(request))
    if not isinstance(outcome, PieceEngineOutcome):
        raise unavailable('piece_engine_outcome_type')
    if (outcome.status != EngineStatus.GENERATED or outcome.artifact is None
            or outcome.artifact_plan is None or outcome.source_meaning is None):
        raise unavailable(outcome.reason_codes[0] if outcome.reason_codes else 'piece_content_unavailable')
    # A GENERATED result is not authority to attach another input's text to
    # this request. Rebind the returned meaning to the complete original,
    # including saved fields/metadata, using the existing CMEE source owner.
    # Hash consistency inside an artifact cannot prove that source relation.
    expected_meaning = build_refined_meaning(request) if refined else build_piece_source_meaning(
        source, expected_owner_id=authenticated_owner_id,
        expected_saved_input_id=original.saved_input_id,
        expected_source_version=original.source_version)
    if (type(outcome.source_meaning) is not type(expected_meaning)
            or outcome.source_meaning != expected_meaning):
        raise unavailable('piece_engine_source_binding')
    expected_plan = _plans(expected_meaning) if refined else compile_piece_artifact_plan(expected_meaning)
    if (type(outcome.artifact_plan) is not type(expected_plan)
            or outcome.artifact_plan != expected_plan):
        raise unavailable('piece_engine_plan_binding')
    if model_candidate is not None:
        from cocolon_meaning_experience_engine.piece_semantic_admission import validate_piece_model_input
        from piece_v2_content_policy import validate_piece_model_preservation
        try:
            blocks = validate_piece_model_input(request, model_candidate)
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError):
            raise unavailable('piece_engine_receipt_binding') from None
        # The actual model bytes, rather than a finite-author replay, are the
        # canonical body. Rehashed substitutions must still match the bound
        # receipt and pass complete independent source/body preservation.
        if (type(outcome.artifact) is not PieceArtifact
                or outcome.artifact.body_blocks != blocks):
            raise unavailable('piece_engine_artifact_binding')
        validate_piece_model_preservation(expected_meaning, expected_plan, outcome.artifact)
        return outcome.artifact.as_candidate()
    # Reuse the sole author, not a second set of text templates. This catches
    # source/plan/result substitutions at the engine-to-B8 seam; it is NOT an
    # independent semantic review of that author or complete PCE-4 safety.
    # Run only during candidate generation, never on save/export/retrieval.
    realize = realize_refined_piece_artifact if refined else realize_piece_artifact
    expected_artifact = realize(
        expected_meaning, expected_plan, tier=tier,
        requested_format=requested_format)
    if (type(outcome.artifact) is not type(expected_artifact)
            or outcome.artifact != expected_artifact):
        raise unavailable('piece_engine_artifact_binding')
    # S7 checks the supplied body against source arguments independently of
    # the author replay above. A matching faulty author cannot certify itself.
    # This finite grammar review does not issue a public safety status.
    validate = validate_refined_preservation if refined else validate_source_meaning_preservation
    validate(expected_meaning, expected_plan, outcome.artifact)
    return outcome.artifact.as_candidate()
