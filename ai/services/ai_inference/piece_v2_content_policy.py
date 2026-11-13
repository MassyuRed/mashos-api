"""B8 candidate policy. Pure, offline-only; not source retrieval or a public gate.

The bounded editorial compiler has no permission to infer missing meaning.
Original and supplemental admission/CMEE integration remain separate work.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from piece_v2_contract import PieceContractError, reconstruct_piece_text
from piece_text_formatter import format_reflection_text

FORMATS = ('short_essay', 'quote', 'declaration')
# Short original inputs remain short; minimum length never authorizes padding.
ENVELOPES = {'short_essay': (1, 420, 6), 'quote': (12, 120, 2),
             'declaration': (12, 180, 4)}


# PCE-4 bounded refusal only. Removing a written name does not verify an
# assertion about the remaining relationship. Require a complete affirmative
# clause; label words inside negation, uncertainty, quotation or conditions
# are not proof of this form. A non-match is never public-safety admission.
_ROLE_ASSERTION = re.compile(
    r'(?:^|[。！？!?\r\n])\s*'
    r'(?:(?:私|わたし|僕|ぼく|俺|おれ)の)?'
    r'(?:友人|同僚|上司|家族|先輩|後輩|知人)'
    r'(?:の(?:友人|同僚|上司|家族|先輩|後輩|知人))*'
    r'[はが]\s*[、,]?\s*'
    r'(?:詐欺師|犯罪者|泥棒|嘘つき|うそつき)\s*'
    r'(?:だった|でした|である|です|だ)\s*(?=[。！？!?\r\n]|\Z)'
)


def unavailable(code: str) -> PieceContractError:
    return PieceContractError('PIECE_CONTENT_UNAVAILABLE', code)


def validate_candidate_text(payload: Mapping) -> str:
    """Validate canonical shape/envelope, not semantic or public acceptance."""
    text = reconstruct_piece_text(payload)
    return _validate_text_envelope(text, payload['body_blocks'], payload['format_type'])


def _validate_text_envelope(text, blocks, format_type):
    """Shared shape limits only; this does not confer any meaning/Safety version."""
    lo, hi, sentences = ENVELOPES[format_type]
    n = len(re.sub(r'\s', '', text))
    if not lo <= n <= hi or len(re.findall(r'[。！？!?]', text)) > sentences:
        raise unavailable('content_envelope')
    if any('\n' in b for b in blocks):
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
    # Detection-only view: never use compatibility normalization or the
    # legacy formatter's display_text as canonical Piece/source bytes. This
    # catches fullwidth contact syntax without folding the visible wording,
    # evidence coordinates, emoji sequences or content hashes.
    result = format_reflection_text(unicodedata.normalize('NFKC', text))
    scan = result.normalized_text
    # Japanese letters are Unicode word characters. ASCII contact syntax can
    # touch them, so the legacy \b / \w boundaries cannot protect this path.
    adjacent_mail = re.search(r'(?i)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', scan)
    adjacent_url = re.search(r'(?i)(?:https?://|www\.)[^\s<>()]+', scan)
    adjacent_handle = re.search(r'(?<![A-Za-z0-9_@])@[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}', scan)
    if (result.flags or result.display_text is None or adjacent_mail
            or adjacent_url or adjacent_handle or _ROLE_ASSERTION.search(scan)):
        raise unavailable('existing_safety_detector')
    if re.search(r'(?i)(?:bearer\s+|(?:api[_ -]?key|password|token)\s*[:=]|postgres(?:ql)?://)', scan):
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


def _piece_model_feeling(text):
    """Read existing complete SELF feelings; never infer from a selection."""
    from piece_v2_expression import _SELF_TOPIC
    from cocolon_meaning_experience_engine.emlis_answer_update import _FEELING, _NOW, _THEN
    now = _NOW.match(text)
    then = _THEN.match(text) if now is None else None
    temporal = now or then
    prefix = temporal.group() if temporal else ''
    value = text[temporal.end():] if temporal else text
    topic = _SELF_TOPIC.fullmatch(value)
    if topic is None or not _FEELING.fullmatch('私は' + topic['body']):
        return None
    finite = re.fullmatch(r'(?P<degree>少し|とても|本当は|まだ|全然|あまり)?'
        r'(?P<stem>嬉し|うれし|寂し|さびし|悲し|苦し|つら|辛|怖|こわ|重|楽し|軽)'
        r'(?P<ending>くなかった|かった|くない|い)(?:です)?', topic['body'])
    if finite is None:
        return None
    ending = finite['ending']
    return ('FEELING', 'SELF', finite['stem'], finite['degree'] or '',
        'negative' if ending.startswith('くな') else 'positive',
        'past' if ending.endswith('かった') else 'nonpast',
        ('NOW', 'も' if 'も' in prefix else 'は') if now else
        ('THEN', prefix) if then else (), topic['speaker'])


def _piece_model_evaluation(text, *, _bound_reference=False):
    """Read a complete written SELF evaluation with the existing Piece owner.

    The original source still needs its normal admission. These temporary
    nodes are parser input for the visible sentence, never evidence/authority
    supplied by the model. Only the established evaluation grammar supplies
    polarity, time and commitment; the entire nominal target stays literal.
    """
    from cocolon_meaning_experience_engine.contracts import MeaningNode, EpistemicState
    from cocolon_meaning_experience_engine.piece_source import (
        PieceSentenceMeaning, _personal_evaluation_shapes,
        _EVALUATIVE_FOCUS, _EVALUATIVE_FINITE, _evaluation_target_references,
        _scoped_expression_match, _TEMPORAL_EVALUATION,
    )
    if _scoped_expression_match(text) or _TEMPORAL_EVALUATION.fullmatch(text):
        return None
    match = _EVALUATIVE_FOCUS.fullmatch(text) or _EVALUATIVE_FINITE.fullmatch(text)
    if match is None or (not _bound_reference and _evaluation_target_references(match['target'])):
        return None
    node = MeaningNode('piece:visible', 'piece:visible', 'PIECE_SOURCE_PROPOSITION',
        'explicit', text, EpistemicState.SOURCE_EXPLICIT, ())
    span = PieceSentenceMeaning(node.node_id, '', 0, len(text), 'source_context')
    try:
        frames = _personal_evaluation_shapes(text, (node,), (span,))
    except PieceContractError:
        return None
    if len(frames) != 1:
        return None
    frame = frames[0]
    if frame.scalar_parts != tuple(match.span(key) for key in ('speaker', 'predicate', 'target')):
        return None
    predicate = text[slice(*frame.scalar_parts[1])]
    # The grammar admits exactly one of its existing degree operators.
    # Retain it separately from the base and inflection, rather than dropping
    # modifiers or equating a negative modal with an affirmative assertion.
    degree = predicate[:predicate.index(match['base'])]
    return ('EVALUATION', 'SELF', frame.construction, frame.kind,
        text[slice(*frame.scalar_parts[2])], match['base'], degree,
        frame.polarity, frame.temporal_scope, frame.commitment, match['speaker'])


def _piece_model_focal(text):
    """Keep the existing complete SELF focal grammar in its original form.

    Predicate wording retains polarity/time/modal scope; the complete target
    stays literal. Named roles/references/scopes still require the S7 owner.
    This does not grant arbitrary unchanged text a semantic interpretation.
    """
    from piece_v2_generation import _FOCUS
    match = _FOCUS.fullmatch(text)
    if match is None:
        return None
    return ('FOCAL', 'SELF', match['predicate'], match['object'], match['speaker'])


def _piece_model_read_active_coordination(raw):
    """Read exactly two active actions sharing the final written past scope.

    Reuse the old body-inverse responsibility: only the connective inflection
    is mapped in a private parser view. The source, receipt and actual output
    are never rewritten, and no source plan/expected sentence is consulted.
    The first affirmative stem does not inherit the last clause's negation.
    """
    from cocolon_meaning_experience_engine import natural_reply_meaning as reader
    if (raw.count('、') != 1 or ',' in raw or '，' in raw
            or reader._UNREAD.search(raw) or reader._DAY.match(raw)):
        return None
    first, second = raw.split('、')
    subject = reader._SUBJECT.match(first)
    if subject is None or subject['noun'] not in reader._SELF or reader._DAY.match(second):
        return None
    narrator = subject['noun']
    second_subject = reader._SUBJECT.match(second)
    if second_subject is not None:
        if second_subject['noun'] != narrator:
            return None
    else:
        second = narrator + 'は' + second

    def active_key(value):
        # The existing whole-clause reader retains exact cases/objects. It
        # must see one complete fact/past active SELF action, not a substring.
        keys = _piece_model_read_block(value + '。')
        if keys is None or len(keys) != 1:
            return None
        key = keys[0]
        if (key[0] != 'FINITE' or key[1:3] != ('SELF', 'SELF')
                or key[5] not in {'伝える', '相談する', '頼む'}
                or key[7:11] != ('fact', 'past', '', 'active')
                or key[-1] != narrator or not key[3].startswith('WRITTEN:')
                or not reader._focus_participant(key[3].removeprefix('WRITTEN:'))
                or len(key[4]) != 1 or key[4][0][0] != 'を'
                or key[11] != (('に', key[3]),)):
            return None
        return key

    final = active_key(second)
    if final is None:
        return None  # No explicit final past means no shared past scope.
    candidates = []
    for stem, past, predicate in (('伝え', '伝えた', '伝える'),
                                  ('相談し', '相談した', '相談する'),
                                  ('頼み', '頼んだ', '頼む')):
        if (not first.endswith(stem)
                or (past, predicate, 'positive', 'fact', 'past', 'active', False)
                not in reader._FORMS):
            continue
        initial = active_key(first[:-len(stem)] + past)
        if initial is not None and initial[5:7] == (predicate, 'positive'):
            candidates.append((initial, final))
    return candidates[0] if len(candidates) == 1 else None


def _piece_model_read_block(text, *, allow_self_omission=False, allow_active_coordination=False):
    """Use the finite reader in the person's voice, not Emlis's voice.

    Every visible clause must be read. Subject completion stays inside this
    block after explicit SELF, when the source was completely explicit SELF.
    A separately enabled whole two-action coordination can share only its
    written final past scope. No output is rewritten.
    """
    from cocolon_meaning_experience_engine import natural_reply_meaning as reader
    from emlis_ai_evidence_ledger_service import _split_source_text
    if type(text) is not str or not text.endswith('。') or reader._top_level_text(text) != text:
        return None
    rows = _split_source_text(text, max_len=max(1, len(text)))
    if not rows:
        return None
    # SELF is still the actor role. The final private key member separately
    # retains this Piece narrator's written spelling, without changing output.
    result, self_context, last_self_speaker = [], False, None
    for row in rows:
        raw = text[row.start:row.end]
        # The ledger excludes a terminal stop; the feeling grammar owns it.
        feeling = _piece_model_feeling(raw + '。')
        evaluation = _piece_model_evaluation(raw + '。')
        focal = _piece_model_focal(raw + '。')
        parsed, count = reader._clauses(raw, 'piece.visible', 'PIECE_OUTPUT', reply=False)
        if feeling is not None or evaluation is not None or focal is not None:
            value = next(value for value in (feeling, evaluation, focal) if value is not None)
            result.append(value)
            self_context = True
            last_self_speaker = value[-1]
            continue
        if len(parsed) != count or len(parsed) != 1:
            if (allow_active_coordination and len(rows) == 1 and row.start == 0
                    and row.end == len(text) - 1):
                coordinated = _piece_model_read_active_coordination(raw)
                if coordinated is not None:
                    return coordinated
            if not allow_self_omission or not self_context or last_self_speaker is None:
                return None
            day = reader._DAY.match(raw)
            start = day.end() if day else 0
            view = raw[:start] + last_self_speaker + 'は' + raw[start:]
            evaluation = _piece_model_evaluation(view + '。')
            if evaluation is not None:
                # The complete typed evaluation owns its target's が; it is
                # not a newly written actor. Reuse only this established SELF
                # context, retaining viewpoint/operators/narrator in the key.
                # The temporary read view never replaces the raw candidate.
                result.append(evaluation)
                continue
            if reader._SUBJECT.match(raw[start:]):
                return None
            feeling = _piece_model_feeling(view + '。')
            parsed, count = reader._clauses(view, 'piece.visible', 'PIECE_OUTPUT', reply=False)
            if feeling is not None:
                result.append(feeling)
                continue
            if len(parsed) != count or len(parsed) != 1:
                return None
        witness = parsed[0]
        # The initial slice changes register/order/SELF repetition only. A
        # focus or voice conversion is not licensed by event-key equality.
        if witness.source_construction != 'PLAIN_FINITE':
            return None
        agent, target, arguments = reader._comparison_event(witness)
        # The existing Emlis comparator drops ni/kara while deriving roles.
        # Retain those written cases here: consultation from someone cannot
        # become consultation to someone merely because names/lemmas match.
        value = witness.raw_text
        day = reader._DAY.match(value)
        value = value[day.end():] if day else value
        subject = reader._SUBJECT.match(value)
        start = subject.end() if subject else 0
        narrator = subject['noun'] if subject and witness.subject == 'SELF' else None
        if witness.subject == 'SELF' and narrator not in reader._SELF:
            return None
        written = set()
        for finite, predicate, polarity, modality, time, voice, receiving in reader._FORMS:
            if (predicate, polarity, modality, time, voice) != (witness.predicate,
                    witness.polarity, witness.modality, witness.temporal_scope, witness.voice):
                continue
            if value.endswith(finite):
                args = reader._arguments(value[start:len(value) - len(finite)])
                if args is not None:
                    written.add(tuple((case, reader._participant(noun, reply=False))
                        for case, noun in args if case in {'に', 'から'}))
        if len(written) != 1:
            return None
        result.append(('FINITE', witness.subject, agent, target, tuple(sorted(arguments)),
            witness.predicate, witness.polarity, witness.modality, witness.temporal_scope,
            witness.relative_day, witness.voice, next(iter(written)), narrator))
        self_context = self_context and witness.subject == 'SELF' if result[:-1] else witness.subject == 'SELF'
        last_self_speaker = narrator
    return tuple(result)


def _piece_model_operator_tree(sentence):
    """Read bounded register edits without normalizing the candidate.

    Every byte belongs either to a recognized complete operator/predicate or
    to an unchanged literal leaf. Literal leaves are retained material, not
    interpreted propositions. In particular a retained conditional/relative
    clause never supplies an inferred actor, cause or completed action.
    Source and candidate are parsed separately; only their full trees compare.
    Quotes and brackets remain with the existing literal/quote-aware S7 arm.
    """
    from piece_v2_expression import _SELF_TOPIC, _WISH_END
    from piece_v2_generation import _OMITTED_ACCOUNT_PREDICATE
    from cocolon_meaning_experience_engine.natural_reply_meaning import _FORMS
    from cocolon_meaning_experience_engine.piece_source import _EVALUATIVE_FINITE

    # Piece-only inflection knowledge, not completed source/candidate pairs.
    # Keep the shared Emlis/Analysis grammar and source admission unchanged.
    # A conjugation class is explicit: guessing it from a polite suffix can
    # conflate distinct verbs (e.g. 降りる / 降る).
    finite_forms = set(_FORMS)
    for lemma, stem, conjugation in (('気づく', '気づ', 'k'),
                                    ('できる', 'でき', 'vowel'),
                                    ('考える', '考え', 'vowel')):
        polite, negative, past = {
            'k': (stem + 'き', stem + 'か', stem + 'いた'),
            'vowel': (stem, stem, stem + 'た'),
        }[conjugation]
        for surface, polarity in ((past, 'positive'),
                (polite + 'ました', 'positive'),
                (negative + 'なかった', 'negative'),
                (polite + 'ませんでした', 'negative')):
            finite_forms.add((surface, lemma, polarity, 'fact', 'past', 'active', False))

    # The te/de form comes from a known active plain past, never a generic
    # kana stem. Aspect stays separate from a completed or negated action.
    state_forms = set()
    for surface, lemma, polarity, modality, time, voice, receiving in finite_forms:
        if ((polarity, modality, time, voice, receiving) ==
                ('positive', 'fact', 'past', 'active', False)
                and not surface.endswith('ました') and surface[-1] in 'ただ'):
            connective = surface[:-1] + ('て' if surface[-1] == 'た' else 'で')
            for suffix, state_polarity in (('います', 'positive'), ('いる', 'positive'),
                    ('いません', 'negative'), ('いない', 'negative')):
                state_forms.add((connective + suffix, connective, lemma, state_polarity))

    if (type(sentence) is not str or not sentence or len(sentence) > 420
            or sentence[-1] not in '。！!'
            or any(c in sentence[:-1] for c in '。！？!?\r\n「」『』"“”（）()【】')):
        return None

    def explicit_topic(value):
        return _SELF_TOPIC.fullmatch(value + '。') is not None

    def feeling_head(value):
        # The whole written target remains separate from the feeling's
        # finite predicate. A passive inside that target is not its owner.
        direct = _piece_model_feeling(value + '。')
        if direct is not None:
            return ('FEELING', direct)
        topic = _SELF_TOPIC.fullmatch(value + '。')
        if topic is None:
            return None
        target, marker, predicate = topic['body'].rpartition('は')
        if not marker or not target.endswith('こと') or not predicate:
            return None
        finite = _piece_model_feeling('私は' + predicate + '。')
        if finite is None:
            return None
        prefix = value[:-len(predicate)]
        return ('TARGET_FEELING', prefix, finite[2:-1])

    def parse(value, *, dependent=False, depth=0):
        if not value or depth > 4:
            return None
        options = set()
        # A single, independently read finite head owns this concession.
        # Other commas are literal content; no split occurs at an arbitrary
        # subject が, nor inside a quote/parenthesis.
        splits = list(re.finditer(r'が[、，,]', value))
        concessions = []
        for split in splits:
            left, right = value[:split.start()], value[split.end():]
            heads = set()
            evaluation = _piece_model_evaluation(left + '。')
            evaluation_form = _EVALUATIVE_FINITE.fullmatch(left + '。')
            # A bare nominal 好き/苦手 can close a source sentence, but it
            # cannot take concessive が without a finite copula/operator.
            if (evaluation is not None and evaluation_form is not None
                    and evaluation_form['inflection']):
                heads.add(('EVALUATION', evaluation))
            feeling = feeling_head(left)
            if feeling is not None:
                heads.add(feeling)
            if len(heads) == 1:
                tail = parse(right, dependent=True, depth=depth + 1)
                if tail is not None:
                    concessions.append(('CONCESSION', next(iter(heads)),
                                        value[split.start():split.end()], tail))
        if len(concessions) > 1:
            return None
        if concessions:
            options.add(concessions[0])

        # These are operator hosts, not assertions about their content.
        # In particular a negated interpretation is not a negative wish.
        impression = re.fullmatch(r'(?P<content>.+)気が(?P<finite>します|する)', value)
        if impression is not None:
            content = impression['content']
            # Require a written clause ending before the host, excluding a
            # suffix inside nominal words such as 湿気/病気 and an empty host.
            if (content[-1] in 'うくぐすつぬぶむるた'
                    or content.endswith(('ない', 'かった'))):
                options.add(('IMPRESSION_HOST', content, '気が',
                             'positive', 'nonpast'))
        interpretation = re.fullmatch(
            r'(?P<content>.+)わけでは(?P<finite>ありません|ない)', value)
        if interpretation is not None and explicit_topic(value):
            content = interpretation['content']
            ending = _WISH_END.search(content)
            # Content with a plain past/copular ending remains literal;
            # no inner proposition is interpreted. Denying an interpretation
            # never denies the embedded action.
            if ((ending is not None and ending.end() == len(content))
                    or content.endswith(('た', 'だ'))):
                options.add(('NEGATED_INTERPRETATION_HOST', content,
                             'わけでは', 'negative', 'nonpast'))

        if explicit_topic(value):
            # Reuse the existing finite verb inventory. The complete prefix
            # including every case, nested nominal, condition and negation
            # is a literal leaf; it is never parsed as a new SELF assertion.
            matches = []
            for surface, lemma, polarity, modality, time, voice, receiving in finite_forms:
                if (modality == 'fact' and time == 'past' and voice == 'active'
                        and not receiving and value.endswith(surface)):
                    prefix = value[:-len(surface)]
                    if prefix and prefix[-1] in 'をにでと':
                        matches.append((len(surface), ('FINITE_WITH_RETAINED_PREFIX',
                            prefix, lemma, polarity, modality, time, voice)))
            if matches:
                longest = max(size for size, _ in matches)
                options.update(key for size, key in matches if size == longest)

            states = []
            for surface, connective, lemma, polarity in state_forms:
                if value.endswith(surface):
                    prefix = value[:-len(surface)]
                    if prefix:
                        states.append((len(surface), ('TE_STATE_WITH_RETAINED_PREFIX',
                            prefix, connective, lemma, polarity, 'nonpast', 'active')))
            if states:
                longest = max(size for size, _ in states)
                options.update(key for size, key in states if size == longest)

            # The source owner already licenses this verbal-noun grammar.
            # Derive its lemma and complete inflection, without adding a
            # topic/verb list or admitting arbitrary kana stems.
            verbal = re.fullmatch(r'(?P<prefix>.+[をにでと])'
                r'(?P<nominal>[一-龥々]{2,})し(?P<finite>ませんでした|ました|なかった|た)', value)
            if verbal is not None:
                negative = verbal['finite'] in ('ませんでした', 'なかった')
                polite = verbal['nominal'] + 'し' + ('ませんでした' if negative else 'ました')
                if _OMITTED_ACCOUNT_PREDICATE.fullmatch(polite):
                    options.add(('FINITE_WITH_RETAINED_PREFIX', verbal['prefix'],
                        verbal['nominal'] + 'する', 'negative' if negative else 'positive',
                        'fact', 'past', 'active'))

        # Reuse the qualified literal-self ending. Preserve its entire
        # lexical content; do not decide whether みたい denotes a wish/simile.
        literal = _WISH_END.search(value)
        if literal is not None and (dependent or explicit_topic(value)):
            ending = literal.group()
            options.add(('LITERAL_SELF_END', value[:literal.start()],
                         ending.removesuffix('です')))

        # A structured parse takes precedence over a mere literal ending
        # enclosing that same concession. Both sides still parse separately.
        if concessions:
            options = {key for key in options if key[0] != 'LITERAL_SELF_END'}
        if len(options) > 1:
            return None
        return next(iter(options)) if options else ('RETAINED', value)

    tree = parse(sentence[:-1])
    return (tree, sentence[-1]) if tree is not None else None


def _piece_model_source_blocks(meaning, plan):
    from cocolon_meaning_experience_engine.piece_source import (
        piece_source_text, piece_text_nodes, validate_piece_saved_fields,
        validate_piece_nominal_references, validate_piece_personal_evaluations,
        validate_piece_expression_scopes,
    )
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifactPlan
    if type(plan) is not PieceArtifactPlan:
        raise unavailable('piece_model_plan_binding')
    validate_piece_saved_fields(meaning)
    validate_piece_nominal_references(meaning)
    validate_piece_personal_evaluations(meaning)
    validate_piece_expression_scopes(meaning)
    nodes = piece_text_nodes(meaning)
    ids = tuple(n.node_id for n in nodes)
    ordered = tuple(n for group in plan.block_node_ids for n in group)
    if (plan.graph_id != meaning.graph.graph_id or plan.source_version != meaning.graph.source_version
            or len(set(ids)) != len(ids) or sorted(ordered) != sorted(ids)
            or tuple(d.node_id for d in plan.duties) != tuple(n.node_id for n in meaning.graph.nodes)):
        raise unavailable('piece_model_plan_binding')
    spans = {span.node_id: span for span in meaning.sentences}
    text = piece_source_text(meaning)
    if set(spans) != set(ids):
        raise unavailable('piece_model_source_binding')
    blocks = []
    for group in plan.block_node_ids:
        if not group:
            raise unavailable('piece_model_plan_binding')
        positions = [ids.index(n) for n in group]
        if positions != list(range(min(positions), max(positions) + 1)):
            raise unavailable('piece_model_plan_binding')
        a, b = spans[group[0]].source_start, spans[group[-1]].source_end
        block = text[a:b]
        if '\n' in block or '\r' in block:
            raise unavailable('piece_model_source_partition')
        blocks.append(block)
    return tuple(blocks)


def _piece_model_topic_continuations(meaning, plan):
    """Source-only, bounded narrator continuity for the model editorial arm.

    Closed impression/denial hosts prove the written narrator's stance,
    never the actor of their retained inner content. Unknown KEEP material
    cannot supply a narrator. This does not change source admission or the
    native author's more conservative editorial decisions.
    """
    from cocolon_meaning_experience_engine.piece_source import (
        piece_source_text, piece_text_nodes, _qualified_self_topic,
        _direct_transitive_expression,
    )
    from cocolon_meaning_experience_engine import natural_reply_meaning as reader
    from piece_v2_expression import _SELF_TOPIC
    from piece_v2_generation import _FOCUS

    _piece_model_source_blocks(meaning, plan)
    original = piece_source_text(meaning)
    nodes = {node.node_id: node for node in piece_text_nodes(meaning)}
    spans = {span.node_id: span for span in meaning.sentences}
    duties = {d.node_id: d.operation for d in plan.duties}
    scopes = {scope.node_id for scope in meaning.expression_scopes}
    evaluations = {frame.node_id: frame for frame in meaning.personal_evaluations}
    positions = {node_id: index for index, node_id in enumerate(nodes)}
    topics = {}
    for node_id, node in nodes.items():
        value = node.value
        if (node_id in scopes or not value.endswith('。')
                or any(c in value for c in '「」『』"\'“”（）()【】;；\r\n')):
            continue
        topic = _SELF_TOPIC.fullmatch(value)
        speaker = None
        operation = duties[node_id]
        if operation == 'SOURCE_PERSONAL_EVALUATION':
            frame = evaluations.get(node_id)
            if frame is not None:
                speaker = original[slice(*frame.scalar_parts[0])]
        elif operation == 'SOURCE_FOCAL_TO_FIRST_PERSON':
            focus = _FOCUS.fullmatch(value)
            if focus is not None:
                speaker = focus['speaker']
        elif operation in {'SOURCE_FIRST_PERSON_TOPIC', 'SOURCE_TRANSITIVE_SELF_TOPIC'}:
            qualified = (_qualified_self_topic(value) if operation == 'SOURCE_FIRST_PERSON_TOPIC'
                         else _direct_transitive_expression(value))
            if qualified is not None:
                speaker = qualified['speaker']
        elif operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' and topic is not None:
            tree = _piece_model_operator_tree(value)
            root = tree[0] if tree is not None else None
            if root is None:
                continue
            if root[0] in {'FINITE_WITH_RETAINED_PREFIX', 'TE_STATE_WITH_RETAINED_PREFIX'}:
                prefix = root[1]
                # Consume the entire known predicate's prefix, not a nearby
                # SELF label. A nested subject/report or an opaque adjunct
                # fails the old complete argument grammar.
                if not prefix.startswith(value[:topic.start('body')]):
                    continue
                arguments = prefix[topic.start('body'):]
                day = reader._DAY.match(arguments)
                arguments = arguments[day.end():] if day else arguments
                parsed = reader._arguments(arguments)
                if parsed is not None and parsed:
                    speaker = topic['speaker']
            elif root[0] in {'IMPRESSION_HOST', 'NEGATED_INTERPRETATION_HOST'}:
                content = root[1]
                head = value[:topic.start('body')]
                if not content.startswith(head):
                    continue
                content = content[len(head):]
                # The outer host owns 気が / わけでは. Other written topics,
                # subjects or SELF viewpoints are not resolved here. なくても
                # remains literal; its も is not a participant inferred by us.
                if (content and not re.search(r'[はが]', content)
                        and not re.search(r'(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が|も|にとって)', content)):
                    speaker = topic['speaker']
        if speaker in reader._SELF:
            topics[node_id] = dict(narrator=speaker,
                topic_end=topic.start('body') if topic is not None and topic['speaker'] == speaker else None)

    continuations = set()
    for group in plan.block_node_ids:
        for previous, current in zip(group, group[1:]):
            before, after = topics.get(previous), topics.get(current)
            if (before is None or after is None or after['topic_end'] is None
                    or before['narrator'] != after['narrator']
                    or positions[current] != positions[previous] + 1
                    or re.search(r'[\r\n]', original[spans[previous].source_end:spans[current].source_start])):
                continue
            # Repetition of a proposition remains a required occurrence;
            # this optional style choice does not collapse duplicate meaning.
            if (before['topic_end'] is not None
                    and nodes[previous].value[before['topic_end']:] == nodes[current].value[after['topic_end']:]):
                continue
            continuations.add(current)
    return topics, frozenset(continuations)


def validate_piece_model_preservation(meaning, plan, artifact):
    """Author-free whole-body review for the bounded model Piece arm.

    The reader is independent of the model and author, not an independent
    general Japanese parser. Unknown source/output clauses cannot pass the
    new finite comparison. Existing S7 may still prove its known scopes in
    full; an unchanged opaque substring is not a general semantic admission.
    """
    from collections import Counter
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact
    from cocolon_meaning_experience_engine.piece_refined import (
        PieceRefinedMeaning, PieceRefinedPlan, refined_source_ref,
    )
    from piece_v2_contract import validate_piece_text_binding
    if (type(artifact) is not PieceArtifact or artifact.format_type != 'short_essay'
            or artifact.eligible_formats != ('short_essay',)):
        raise unavailable('piece_model_artifact_binding')
    validate_piece_text_binding(artifact.content_payload(), artifact.piece_text, artifact.piece_text_hash)
    validate_candidate_text(artifact.content_payload())
    if type(meaning) is PieceRefinedMeaning:
        if (type(plan) is not PieceRefinedPlan or plan.source_ref != meaning.source_ref
                or meaning.source_ref != refined_source_ref(meaning.source)
                or plan.source_roles != ('ORIGINAL_USER_INPUT', 'SUPPLEMENTAL_ANSWER')
                or plan.eligible_formats != ('short_essay',)):
            raise unavailable('piece_model_source_binding')
        parts = ((meaning.original, plan.original_plan), (meaning.supplemental, plan.supplemental_plan))
    else:
        parts = ((meaning, plan),)
    offset = 0
    for part, child_plan in parts:
        source_blocks = _piece_model_source_blocks(part, child_plan)
        blocks = artifact.body_blocks[offset:offset + len(source_blocks)]
        offset += len(source_blocks)
        if len(blocks) != len(source_blocks):
            raise unavailable('piece_model_block_partition')
        # Existing named-person abstraction and reference dependencies remain
        # owned by S7. Event-key comparison alone must not retain a raw name
        # or reorder the antecedent of "その..." across its dependent clause.
        complete = not (part.role_bindings or part.nominal_references or part.expression_scopes)
        for source_text, output_text in zip(source_blocks, blocks, strict=True):
            source = _piece_model_read_block(source_text)
            all_self = source is not None and all(row[1] == 'SELF' for row in source)
            visible = _piece_model_read_block(output_text, allow_self_omission=all_self,
                                              allow_active_coordination=all_self)
            if source is None or visible is None or Counter(source) != Counter(visible):
                complete = False
                break
            if source != visible and not all_self:
                complete = False
                break
        if not complete:
            text = '\n\n'.join(blocks)
            import hashlib
            child = PieceArtifact(blocks, text, hashlib.sha256(text.encode()).hexdigest(),
                                  'short_essay', ('short_essay',))
            try:
                try:
                    validate_source_meaning_preservation(part, child_plan, child)
                except PieceContractError:
                    validate_source_meaning_preservation(part, child_plan, child, _model_register=True)
            except PieceContractError:
                raise unavailable('piece_model_meaning_unassessed_or_changed') from None
    if offset != len(artifact.body_blocks):
        raise unavailable('piece_model_block_partition')
    check_existing_detectors(artifact.piece_text)


def validate_source_meaning_preservation(meaning, plan, artifact, *, _model_register=False) -> None:
    """Inspect a Piece artifact against source arguments, without author replay.

    The existing source owner supplies validated explicit grammar and spans.
    This review checks complete proposition multiplicity, argument order,
    predicate wording (including negation/time/modality), written scope and
    public role identity. Only the current finite editorial operations are
    recognized; it is not a general paraphrase judge or public-safety issuer.
    Nothing here produces/rewrites a candidate, calls an author/plan compiler,
    reads stored data, or grants ready/adjusted. Source-parser independence and
    an independent human review are NOT claimed by this author-free check.
    The default native contract stays literal. Only the model review can
    request the bounded, source-anchored register comparisons below.
    """
    from cocolon_meaning_experience_engine.piece_semantic_admission import PieceSemanticSnapshotV1
    if type(meaning) is PieceSemanticSnapshotV1:
        # Source identity includes the P1 tier; this path performs review only.
        import json
        from cocolon_meaning_experience_engine.piece_semantic_admission import _request
        from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
        source = meaning.source_snapshot
        for tier in ('free', 'plus', 'premium'):
            req = PieceGenerationRequest('review-private-piece', source, source.owner_id,
                source.saved_input_id, source.source_version, tier=tier)
            if _request(req).request_id == meaning.request_ref:
                return validate_piece_semantic_preservation(meaning, plan, artifact,
                    tier=tier, requested_format=None)
        raise unavailable('piece_semantic_request_binding')
    from piece_v2_contract import validate_piece_text_binding
    from piece_v2_generation import _FOCUS, _is_unpunctuated_account
    from piece_v2_expression import _SELF_TOPIC, _WISH_END
    from cocolon_meaning_experience_engine.piece_source import (
        PieceSourceMeaning, _direct_transitive_expression, _PERSON_NAME_LEFT_BOUNDARY,
        piece_public_role_aliases, validate_piece_saved_fields,
        validate_piece_nominal_references, validate_piece_personal_evaluations,
        validate_piece_expression_scopes,
        piece_text_nodes, piece_source_text, _scoped_self_topic, _qualified_self_topic,
        _scoped_finite_self_person_action,
    )
    from cocolon_meaning_experience_engine.piece_v1c import PieceArtifact, PieceArtifactPlan

    def reject():
        raise unavailable('piece_meaning_not_preserved')

    from cocolon_meaning_experience_engine.piece_refined import PieceSupplementalMeaning
    if (type(meaning) not in (PieceSourceMeaning, PieceSupplementalMeaning) or type(plan) is not PieceArtifactPlan
            or type(artifact) is not PieceArtifact):
        reject()
    validate_piece_saved_fields(meaning)
    validate_piece_nominal_references(meaning)
    validate_piece_personal_evaluations(meaning)
    validate_piece_expression_scopes(meaning)
    validate_piece_text_binding(artifact.content_payload(), artifact.piece_text,
                                artifact.piece_text_hash)
    original = piece_source_text(meaning)
    nodes = meaning.graph.nodes
    ids = tuple(node.node_id for node in nodes)
    ordered = tuple(node_id for group in plan.block_node_ids for node_id in group)
    if (plan.graph_id != meaning.graph.graph_id
            or plan.source_version != meaning.graph.source_version
            or len(set(ids)) != len(ids) or sorted(ordered) != sorted(ids)
            or tuple(d.node_id for d in plan.duties) != ids
            or len(artifact.body_blocks) != len(plan.block_node_ids)
            or not ids or any(not group for group in plan.block_node_ids)):
        reject()
    spans = {s.node_id: s for s in meaning.sentences}
    text_nodes = piece_text_nodes(meaning)
    if set(spans) != {n.node_id for n in text_nodes} or len(meaning.evidence) != len(text_nodes):
        reject()
    for node, evidence in zip(text_nodes, meaning.evidence, strict=True):
        span = spans[node.node_id]
        if (original[span.source_start:span.source_end] != node.value
                or node.evidence_ids != (evidence.evidence_id,)
                or meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                != node.value.encode('utf-8')):
            reject()
    if meaning.saved_snapshot is not None:
        # Independently retain every field/complete-line boundary from the
        # original spans. A forged plan cannot concatenate those paragraphs.
        paragraphs = []
        previous = None
        for node, evidence in zip(text_nodes, meaning.evidence, strict=True):
            span = spans[node.node_id]
            if (previous is None or evidence.field_path != previous[0]
                    or re.search(r'[\r\n]', original[previous[1]:span.source_start])):
                paragraphs.append([])
            paragraphs[-1].append(node.node_id)
            previous = (evidence.field_path, span.source_end)
        if plan.block_node_ids != tuple(tuple(group) for group in paragraphs):
            reject()

    # Match source nouns to their already-proved public role, never infer a
    # relationship or replace a detected unsafe token with a generic phrase.
    aliases = piece_public_role_aliases(meaning.role_bindings)
    phrases = {}
    for binding in meaning.role_bindings:
        phrase = binding.role + 'の' + binding.name
        if original[binding.source_start:binding.source_end] != phrase:
            reject()
        phrases[phrase] = aliases[binding.name]
    replacements = {**phrases, **aliases}
    matcher = None
    if aliases:
        matcher = re.compile('|'.join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
                             + '|' + _PERSON_NAME_LEFT_BOUNDARY + '(?:'
                             + '|'.join(re.escape(n) for n in sorted(aliases, key=len, reverse=True)) + ')')

    def anchor(fragment):
        """An escaped matching pattern, not generated Piece text."""
        if matcher is None:
            return re.escape(fragment)
        parts, end = [], 0
        for match in matcher.finditer(fragment):
            parts.extend((re.escape(fragment[end:match.start()]),
                          re.escape(replacements[match.group()])))
            end = match.end()
        return ''.join(parts) + re.escape(fragment[end:])

    def transitive_predicate(predicate):
        if _model_register:
            from piece_v2_generation import _transitive_predicate_forms
            finite, _, _ = _transitive_predicate_forms()
            plain = predicate[:-2] if predicate.endswith('です') else predicate
            if plain.endswith(('たい', 'たくない')) and plain in finite and plain + 'です' in finite:
                # Only the existing whole wish predicate changes register.
                # Its object, polarity and every enclosing source scope stay anchored.
                return anchor(plain) + '(?:です)?'
        return anchor(predicate)

    def same_undecided(source, visible):
        # A source-bound decision target is retained byte-for-byte. This is
        # only the existing nonpast negative 決めている register pair, not a
        # parser for arbitrary negative statements or an inferred reservation.
        match = re.fullmatch(r'(?P<prefix>まだ[、，,][^。！？!?「」『』"\r\n、，,]+(?:かは|[一-龥々ァ-ヴー]+は))'
                             r'決めて(?:いません|いない)。', source)
        if match is None:
            return False
        return re.fullmatch(anchor(match['prefix']) + r'決めて(?:いません|いない)。', visible) is not None

    def same_literal_self_register(source, visible):
        # Reuse the qualified literal self-account owner, including its
        # explicit narrator and complete ending. The entire source argument
        # stays anchored; only optional polite です changes. This neither
        # classifies a simile as a wish nor borrows a narrator or source.
        from cocolon_meaning_experience_engine.piece_source import _literal_self_account
        if not _literal_self_account(source):
            return False
        head = source[:-1]
        bare = head[:-2] if head.endswith('です') else head
        return re.fullmatch(anchor(bare) + r'(?:です)?' + re.escape(source[-1]), visible) is not None

    def same_operator_tree(source, visible):
        # Parse untouched source/output independently. Only literal leaves
        # can use S7's already-proved public alias; typed operators, narrator,
        # inflection axes, order and punctuation must remain identical.
        # Never publicize the source first and reparse a manufactured view.
        literal_fields = {
            ('RETAINED', 2): (1,),
            ('TARGET_FEELING', 3): (1,),
            ('IMPRESSION_HOST', 5): (1,),
            ('NEGATED_INTERPRETATION_HOST', 5): (1,),
            ('FINITE_WITH_RETAINED_PREFIX', 7): (1,),
            ('TE_STATE_WITH_RETAINED_PREFIX', 7): (1,),
            ('LITERAL_SELF_END', 3): (1,),
            ('EVALUATION', 11): (4,),
        }

        def same(left, right):
            if type(left) is not type(right):
                return False
            if type(left) is not tuple:
                return left == right
            if len(left) != len(right):
                return False
            fields = literal_fields.get((left[0], len(left)), ()) if left and type(left[0]) is str else ()
            return all(re.fullmatch(anchor(a), b) is not None if i in fields
                       else same(a, b) for i, (a, b) in enumerate(zip(left, right, strict=True)))

        source_tree = _piece_model_operator_tree(source)
        visible_tree = _piece_model_operator_tree(visible)
        return source_tree is not None and visible_tree is not None and same(source_tree, visible_tree)

    def same_finite_model_context(node_id, source, visible):
        # A mixed original can retain an opaque KEEP clause while another
        # field changes only the known finite register. Keep the full S7
        # source/plan/partition checks; compare this complete node with the
        # existing reader, never a partial source or an inferred narrator.
        if (node_id in scopes or node_id in evaluations
                or any(node_id in (r.antecedent_node_id, r.reference_node_id)
                       for r in meaning.nominal_references)
                or anchor(source) != re.escape(source)):
            return False
        expected = _piece_model_read_block(source)
        if expected is None or len(expected) != 1:
            return False
        key = expected[0]
        if (key[0] != 'FINITE' or key[1] != 'SELF'
                or key[-1] not in ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
                or key[5] not in ('頼む', '相談する', '伝える')
                or key[7:11] != ('fact', 'past', '', 'active')):
            return False
        return _piece_model_read_block(visible) == expected

    def same_scoped_finite_model_context(node_id, source, visible):
        # Source owns the complete outer relation and inner action together.
        # Retain every premise/argument byte, including its narrator/cases;
        # the existing finite reader compares only the completed predicate's
        # register. No topic omission, fronting or argument reorder follows.
        from cocolon_meaning_experience_engine.natural_reply_meaning import _FORMS
        scope = scopes.get(node_id)
        match = _scoped_finite_self_person_action(source)
        if scope is None or match is None or anchor(source) != re.escape(source):
            return False
        prefix = source[:match.start('intention')]
        if not visible.startswith(prefix) or not visible.endswith('。'):
            return False
        inner = match['intention']
        expected = _piece_model_read_block(inner)
        if expected is None or len(expected) != 1:
            return False
        key = expected[0]
        if key[0] != 'FINITE' or key[1] != 'SELF' or key[7:11] != ('fact', 'past', '', 'active'):
            return False
        forms = [form for form, lemma, polarity, modality, temporal, voice, receiving in _FORMS
                 if not receiving and inner.endswith(form + '。')
                 and (lemma, polarity, modality, temporal, voice) == (
                     key[5], key[6], key[7], key[8], key[10])]
        if len(forms) != 1:
            return False
        argument_prefix = inner[:-len(forms[0])-1]
        remainder = visible[len(prefix):]
        return remainder.startswith(argument_prefix) and _piece_model_read_block(remainder) == expected

    def same_literal_reason_value(node_id, source, visible):
        # A qualified opaque KEEP may contain a complete self reason/value.
        # Retain its literal premise, relation and entire modified target;
        # compare only the existing affirmative copula register. This is not
        # a new typed reason/value interpretation or source admission rule.
        from cocolon_meaning_experience_engine.piece_source import (
            _scoped_expression_match, _EVALUATIVE_FINITE, _same_self_scope_author,
        )
        if (node_id in scopes or node_id in evaluations
                or any(node_id in (r.antecedent_node_id, r.reference_node_id)
                       for r in meaning.nominal_references)
                or anchor(source) != re.escape(source)):
            return False
        scoped = _scoped_expression_match(source)
        if scoped is None or scoped['marker'] != 'ので':
            return False
        expression = scoped['intention']
        value = _EVALUATIVE_FINITE.fullmatch(expression)
        if (value is None or value['construction'] != 'は'
                or value['base'] not in {'大切', '大事', '重要', '必要'}
                or value['copula'] not in {'です', 'だ'}
                or value['inflection'] != value['copula']
                or re.search(r'[はがも、，,。！？!?「」『』"“”\r\n]', value['target'])
                or re.search(r'私|わたし|僕|ぼく|俺|おれ', value['target'])
                or not _same_self_scope_author(scoped['premise'], value['speaker'])):
            return False
        # Only this same sentence's literally proved author can be elided.
        # Exact slicing also retains the source comma, spacing and terminal.
        topic = value['speaker'] + 'は'
        prefix = source[:scoped.start('intention')]
        body = expression[len(topic):value.start('copula')]
        return re.fullmatch(re.escape(prefix) + '(?:' + re.escape(topic) + ')?'
                            + re.escape(body) + r'(?:です|だ)'
                            + re.escape(source[-1]), visible) is not None

    def same_evaluation(node_id, visible, author, viewpoint, prefix, optional_prefix,
                        *, source_expression=None):
        frame = evaluations[node_id]
        from cocolon_meaning_experience_engine.piece_source import _EVALUATIVE_FOCUS
        expression = source_nodes[node_id].value if source_expression is None else source_expression
        focal = _EVALUATIVE_FOCUS.fullmatch(expression)
        if focal is not None:
            # A qualified evaluation may keep its complete source focal order.
            # Anchor every word, narrator, viewpoint and inner operator; only
            # its outer present copula changes register. The caller retains
            # the complete written scope, field and paragraph boundaries.
            original_order = (anchor(expression[:focal.start('copula')])
                              + r'(?:です|だ)' + anchor(expression[focal.end('copula'):]))
            if re.fullmatch(original_order, visible) is not None:
                return True
        _, _, target = (original[a:b] for a, b in frame.scalar_parts)
        # Source validation above owns the reference edges and public aliases.
        # No other target particle, argument, speaker or clause can enter this view.
        body = anchor(target) + r'が(?P<evaluation_predicate>[^。！？!?]+)' + re.escape(source_nodes[node_id].value[-1])
        if re.fullmatch(optional_prefix + body, visible) is None:
            return False
        view = visible if re.fullmatch(prefix + body, visible) is not None else author + viewpoint + visible
        source_key = _piece_model_evaluation(
            source_nodes[node_id].value if source_expression is None else source_expression,
            _bound_reference=True)
        visible_key = _piece_model_evaluation(view, _bound_reference=True)
        if source_key is None or visible_key is None:
            return False
        # が-focus -> は-topic is already the native preference operation;
        # explicit にとって remains a distinct value viewpoint. The target
        # itself was matched against the entire public source anchor above.
        source_view = 'は' if source_key[2] == 'が' else source_key[2]
        return (source_view == visible_key[2] and source_key[:2] == visible_key[:2]
            and source_key[3] == visible_key[3] and source_key[5:] == visible_key[5:])

    evaluations = {f.node_id: f for f in meaning.personal_evaluations}
    scopes = {s.node_id: s for s in meaning.expression_scopes}
    duties = {d.node_id: d.operation for d in plan.duties}
    source_nodes = {n.node_id: n for n in nodes}
    positions = {node_id: i for i, node_id in enumerate(ids)}
    model_topics, model_continuations = (_piece_model_topic_continuations(meaning, plan)
                                        if _model_register else ({}, frozenset()))

    def arguments(node_id, expression):
        stop = re.escape(source_nodes[node_id].value[-1])
        frame = evaluations.get(node_id)
        if frame is not None:
            author, predicate, target = (original[a:b] for a, b in frame.scalar_parts)
            finite = predicate[:-1] + frame.copula if predicate.endswith('な') else predicate
            viewpoint = 'にとって' if frame.construction == 'にとって' else 'は'
            return author, viewpoint, anchor(target) + 'が' + anchor(finite) + stop, None
        focal = _FOCUS.fullmatch(expression)
        direct = _direct_transitive_expression(expression) if focal is None else None
        if focal is not None or direct is not None:
            parsed = focal if focal is not None else direct
            target = parsed['object'].lstrip('、，,') if focal is not None else parsed['object']
            predicate = (transitive_predicate(parsed['predicate']) if node_id not in scopes
                         else anchor(parsed['predicate']))
            return parsed['speaker'], 'は', anchor(target) + 'を' + predicate + stop, None
        topic = (_scoped_self_topic(expression) if node_id in scopes
                 else _qualified_self_topic(expression))
        if topic is None:
            reject()
        kind = 'wish' if _WISH_END.search(topic['body']) else 'literal'
        if kind == 'literal' and node_id not in scopes:
            reject()
        return topic['speaker'], 'は', anchor(topic['body']) + stop, kind

    for group, block in zip(plan.block_node_ids, artifact.body_blocks, strict=True):
        if '「' in block:
            # Reuse the same existing quote-boundary asset as source intake,
            # not its source classification or author. The complete quoted
            # proposition must still match its literal KEEP duty below.
            from emlis_ai_grounded_sentence_surface import _body_sentence_spans
            sentences, cursor = [], 0
            for _, end in _body_sentence_spans(block):
                # Preserve gaps the witness trims. Source intake retains
                # Unicode spaces outside its established horizontal lstrip;
                # candidate comparison must keep those exact same bytes.
                sentences.append(block[cursor:end])
                cursor = end
        else:
            sentences = re.findall(r'[^。！？!?]+[。！？!?]', block)
        covered = ''.join(sentences)
        final_id = group[-1]
        if (covered != block and block.startswith(covered)
                and meaning.saved_snapshot is not None
                and duties[final_id] == 'KEEP_COMPLETE_SOURCE_CONTEXT'
                and _is_unpunctuated_account(source_nodes[final_id].value)):
            # A source-bound paragraph may end in its complete action line
            # without a stop. The exact KEEP check still rejects text edits.
            sentences.append(block[len(covered):])
        if ''.join(sentences) != block or len(sentences) != len(group):
            reject()
        previous_id, previous_author = None, None
        for node_id, visible in zip(group, sentences, strict=True):
            node, operation = source_nodes[node_id], duties[node_id]
            if (node_id in scopes and _scoped_finite_self_person_action(node.value) is not None
                    and operation != 'KEEP_COMPLETE_SOURCE_CONTEXT'):
                reject()
            topic = model_topics.get(node_id)
            if (_model_register and node_id in model_continuations and topic is not None
                    and previous_id is not None and previous_author == topic['narrator']
                    and positions[node_id] == positions[previous_id] + 1):
                # Only an accepted same-narrator chain supplies this private
                # parse view. Restore the exact source topic, not an inferred
                # actor; the raw visible sentence is never changed.
                view = node.value[:topic['topic_end']] + visible
                if (same_literal_self_register(node.value, view)
                        or same_operator_tree(node.value, view)):
                    previous_id, previous_author = node_id, topic['narrator']
                    continue
            if operation == 'KEEP_COMPLETE_SOURCE_CONTEXT':
                if (re.fullmatch(anchor(node.value), visible) is None
                        and not (_model_register and (
                            same_undecided(node.value, visible)
                            or same_finite_model_context(node_id, node.value, visible)
                            or same_scoped_finite_model_context(node_id, node.value, visible)
                            or same_literal_reason_value(node_id, node.value, visible)
                            or same_operator_tree(node.value, visible)))):
                    reject()
                previous_id = node_id
                previous_author = topic['narrator'] if topic is not None else None
                continue
            if operation not in {
                    'SOURCE_FIRST_PERSON_TOPIC', 'SOURCE_TRANSITIVE_SELF_TOPIC',
                    'SOURCE_FOCAL_TO_FIRST_PERSON', 'SOURCE_PERSONAL_EVALUATION',
                    'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'}:
                reject()
            scope = scopes.get(node_id)
            if (operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON') != (scope is not None):
                reject()
            if (_model_register and operation == 'SOURCE_FIRST_PERSON_TOPIC'
                    and (same_literal_self_register(node.value, visible)
                         or same_operator_tree(node.value, visible))):
                previous_id = node_id
                previous_author = _scoped_self_topic(node.value)['speaker']
                continue
            expression = original[slice(*scope.expression_scalar_span)] if scope else node.value
            author, viewpoint, body, topic_kind = arguments(node_id, expression)
            prefix = re.escape(author + viewpoint) + '[、，,]?'
            same_author = (previous_id is not None and previous_author == author
                           and positions[node_id] == positions[previous_id] + 1
                           and not re.search(r'[\r\n]', original[
                               spans[previous_id].source_end:spans[node_id].source_start]))
            # This only recognizes an already explicit adjacent author. It
            # never infers the first author, crosses a field/paragraph/newline,
            # or elides an explicit にとって value viewpoint.
            optional_prefix = '(?:' + prefix + ')?' if same_author and viewpoint == 'は' else prefix
            if _model_register and node_id in evaluations and scope is None:
                # Reuse native same-author continuity. The full source target,
                # literal narrator and every evaluation operator still match.
                if not same_evaluation(node_id, visible, author, viewpoint, prefix, optional_prefix):
                    reject()
                previous_id, previous_author = node_id, author
                continue
            if (_model_register and node_id in evaluations and scope is not None
                    and scope.relation == 'SOURCE_EXPLICIT_TIME_CONTEXT'
                    and evaluations[node_id].kind == 'PERSONAL_PREFERENCE'
                    and evaluations[node_id].construction == 'は'):
                # The source owner already bound the outer time and inner
                # evaluation separately. Keep the entire written time topic,
                # marker and separator. Only the already-proved adjacent
                # same-author topic may be omitted; the first narrator and
                # field/paragraph boundaries retain their existing checks.
                outer = original[spans[node_id].source_start:scope.expression_scalar_span[0]]
                if (not visible.startswith(outer)
                        or not same_evaluation(node_id, visible[len(outer):], author,
                            viewpoint, prefix, optional_prefix, source_expression=expression)):
                    reject()
                previous_id, previous_author = node_id, author
                continue
            literal_emphasis = False
            if scope is None:
                pattern = optional_prefix + body
            else:
                premise = original[slice(*scope.scope_scalar_span)]
                if premise.startswith(author + 'は') and viewpoint == 'は':
                    optional_prefix = '(?:' + prefix + ')?'
                premise_pattern = anchor(premise) + '、'
                pattern = premise_pattern + optional_prefix + body
                # Existing simple-wish grammar may front its self topic, but
                # an explicit concession/reference keeps the premise first.
                referenced = any(ref.reference_node_id == node_id
                                 and scope.scope_scalar_span[0] <= ref.reference_scalar_span[0]
                                 and ref.reference_scalar_span[1] <= scope.scope_scalar_span[1]
                                 for ref in meaning.nominal_references)
                premise_first = scope.relation == 'SOURCE_EXPLICIT_CONCESSION' or referenced
                if topic_kind == 'literal':
                    # Scoped literal comparisons already have an explicit
                    # first person and complete predicate. Match the same
                    # authored clause order without granting topic omission.
                    pattern = (premise_pattern + prefix if premise_first
                               else prefix + premise_pattern) + body
                    if node.value.endswith(('！', '!')):
                        # Match the complete literal source only. Its words,
                        # subject, scope order and emphasis remain source-
                        # owned; no inferred wish or author omission follows.
                        pattern = anchor(node.value)
                        literal_emphasis = True
                elif topic_kind == 'wish' and not premise_first:
                    pattern = '(?:' + pattern + '|' + optional_prefix + premise_pattern + body + ')'
            if re.fullmatch(pattern, visible) is None:
                if (_model_register and node_id in evaluations and scope is not None
                        and scope.relation in {'SOURCE_EXPLICIT_REASON',
                            'SOURCE_EXPLICIT_CONDITION', 'SOURCE_EXPLICIT_CONCESSION'}):
                    # The source already owns this evaluation and its outer
                    # relation. Retain the complete public source prefix and
                    # compare the remaining evaluation with the existing
                    # operator/target reader. Keep native matches first and
                    # reuse only their already-proved author continuity.
                    outer = original[spans[node_id].source_start:scope.expression_scalar_span[0]]
                    outer_match = re.match(anchor(outer), visible)
                    if (outer_match is not None
                            and same_evaluation(node_id, visible[outer_match.end():], author,
                                viewpoint, prefix, optional_prefix, source_expression=expression)):
                        previous_id, previous_author = node_id, author
                        continue
                if (_model_register and scope is not None
                        and topic_kind in {'wish', 'literal'}):
                    # The qualified scoped self account already owns every
                    # word, its explicit narrator and the whole outer prefix.
                    # Reuse the existing literal self register pair in source
                    # order, without reclassifying a literal as a wish. Do not
                    # change its scope, omit its author or extend emphasized
                    # literal clauses' narrator continuity.
                    outer = original[spans[node_id].source_start:scope.expression_scalar_span[0]]
                    outer_match = re.match(anchor(outer), visible)
                    if (outer_match is not None
                            and same_literal_self_register(expression, visible[outer_match.end():])):
                        previous_id, previous_author = node_id, None if literal_emphasis else author
                        continue
                    if not premise_first and not literal_emphasis:
                        # Native scoped self accounts already allow this
                        # explicit author before the complete premise. Reuse
                        # that same position and the literal ending comparison;
                        # the temporary view is only for review, never output.
                        front = re.match(prefix + premise_pattern, visible)
                        if front is not None:
                            topic = _scoped_self_topic(expression)
                            view = expression[:topic.start('body')] + visible[front.end():]
                            if same_literal_self_register(expression, view):
                                previous_id, previous_author = node_id, author
                                continue
                # The existing focal grammar also owns its original order.
                # Compare source anchors; never construct or rewrite prose.
                focal = _FOCUS.fullmatch(expression) if _model_register else None
                if focal is None:
                    reject()
                head = expression[:-1]
                copula_size = 2 if head.endswith('です') else 1
                original_order = anchor(head[:-copula_size]) + '(?:です|だ)' + re.escape(expression[-1])
                if scope is not None:
                    original_order = anchor(original[slice(*scope.scope_scalar_span)]) + '、' + original_order
                # A qualified focal wish may retain its explicit が subject
                # in direct order. This is a source-bound model comparison,
                # not a new source grammar or a rewrite to は. Past/modal and
                # scoped focal expressions retain their existing comparisons.
                direct_ga = False
                if (operation == 'SOURCE_FOCAL_TO_FIRST_PERSON' and scope is None
                        and focal['past_predicate'] is None and focal['modal'] is None):
                    from piece_v2_generation import _transitive_predicate_forms
                    finite, _, _ = _transitive_predicate_forms()
                    predicate = focal['predicate']
                    if (predicate.endswith(('たい', 'たくない'))
                            and predicate in finite and predicate + 'です' in finite):
                        direct_ga = re.fullmatch(re.escape(author + 'が') + '[、，,]?' + body,
                                                 visible) is not None
                if not direct_ga and re.fullmatch(original_order, visible) is None:
                    reject()
            previous_id, previous_author = node_id, None if literal_emphasis else author


def validate_piece_semantic_preservation(snapshot, plan, artifact, *, tier, requested_format):
    """P4 author-free review of actual private blocks and their source duties.

    No compiler/realizer/candidate acquisition is called. Source-scope validation
    is shared with admission; parser independence or general paraphrase review
    is not claimed. The closed arm allows no source-to-text lexical changes.
    """
    import hashlib
    import json
    from dataclasses import asdict
    from cocolon_meaning_experience_engine.piece_semantic_admission import (
        PieceSemanticPlanV1, PieceSemanticArtifactV1, PieceSemanticRealizationV1,
        PLAN_SCHEMA, ARTIFACT_SCHEMA, MEANING_VERSION, PROFILE,
        canonical, digest, require, validate_snapshot_self, source_nodes,
    )
    validate_snapshot_self(snapshot)
    require(type(plan) is PieceSemanticPlanV1, 'piece_semantic_plan_type')
    nodes = source_nodes(snapshot)
    expected_duties = [dict(duty_ref='duty:' + b.claim_ref, claim_refs=[b.claim_ref],
        node_refs=[b.node_ref], source_binding_refs=[b.source_binding_ref],
        required_scope_refs=json.loads(b.claim_json)['polarity']['scope_refs'],
        operation='KEEP_COMPLETE_SOURCE_CONTEXT') for b in snapshot.claim_bindings]
    groups = (tuple(n[0] for n in nodes[:-1]), (nodes[-1][0],))
    selection_refs = tuple('selection:' + '|'.join(r.alias_refs) for r in snapshot.source_selections)
    expected_plan = dict(schema_version=PLAN_SCHEMA, semantic_profile=PROFILE,
        snapshot_ref=snapshot.snapshot_ref, source_commitment=snapshot.source_commitment,
        graph_id='piece-graph:' + digest([snapshot.snapshot_ref,[n[0] for n in nodes]]),
        duties=expected_duties,block_node_ids=groups,selection_duties=selection_refs,
        eligible_formats=('short_essay',),intent='USER_OWNED_COCOLON_SHAPED')
    require(canonical(asdict(plan))==canonical(expected_plan), 'piece_semantic_plan_coverage')
    selected = choose_format(tier=tier,requested=requested_format,
                             eligible=plan.eligible_formats,recommended='short_essay')
    if artifact is None:
        return
    require(type(artifact) is PieceSemanticArtifactV1, 'piece_semantic_artifact_type')
    require((artifact.schema_version,artifact.semantic_profile,artifact.meaning_contract_version)==
            (ARTIFACT_SCHEMA,PROFILE,MEANING_VERSION),'piece_semantic_artifact_namespace')
    require(artifact.snapshot_ref==snapshot.snapshot_ref and artifact.plan_ref==plan.plan_ref
            and artifact.source_commitment==snapshot.source_commitment
            and artifact.format_type==selected and artifact.eligible_formats==plan.eligible_formats
            and artifact.retained_selection_refs==selection_refs,'piece_semantic_artifact_binding')
    require(type(artifact.body_blocks) is tuple and len(artifact.body_blocks)==len(groups)
            and all(type(b) is str and b for b in artifact.body_blocks),'piece_semantic_blocks')
    # Inspect the entire visible source interval, including every connective;
    # checking the six isolated predicates alone would miss an invented cause.
    locations = {}
    by_node = {n[0]:n for n in nodes}
    for bi, group in enumerate(groups):
        offset = 0
        for node_ref in group:
            _, field, start, end, source_text = by_node[node_ref]
            require(artifact.body_blocks[bi][offset:offset+len(source_text)]==source_text,
                    'piece_semantic_visible_scope')
            locations[node_ref]=(bi,offset,start)
            offset += len(source_text)
        require(offset==len(artifact.body_blocks[bi]),'piece_semantic_extra_visible_meaning')
    require(artifact.piece_text=='\n\n'.join(artifact.body_blocks)
            and artifact.piece_text_hash==hashlib.sha256(artifact.piece_text.encode()).hexdigest(),
            'piece_semantic_text_binding')
    expected_realizations=[]
    for b in snapshot.claim_bindings:
        bi,offset,base=locations[b.node_ref]
        a=offset+b.scalar_start-base;end=offset+b.scalar_end-base
        require(artifact.body_blocks[bi][a:end]==json.loads(b.claim_json)['text'],
                'piece_semantic_claim_visible_binding')
        expected_realizations.append(dict(claim_ref=b.claim_ref,duty_ref='duty:'+b.claim_ref,
            node_refs=[b.node_ref],source_binding_refs=[b.source_binding_ref],
            block_index=bi,visible_scalar_start=a,visible_scalar_end=end))
    require(all(type(r) is PieceSemanticRealizationV1 for r in artifact.claim_realizations)
            and canonical([asdict(r) for r in artifact.claim_realizations])==canonical(expected_realizations),
            'piece_semantic_visible_trace')
    _validate_text_envelope(artifact.piece_text,artifact.body_blocks,artifact.format_type)
    check_existing_detectors(artifact.piece_text)
