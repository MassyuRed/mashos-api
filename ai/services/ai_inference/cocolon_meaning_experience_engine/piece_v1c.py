"""CMEE's code-disabled Piece consumer: graph -> intent/plan -> canonical body.

The existing B8 caller and B9 image path consume this result. No Emlis body is
created or reused. This bounded consumer has no authentication, DB, quota,
public route, native renderer or external-generation capability.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from piece_v2_contract import PieceContractError
from piece_v2_content_policy import (
    ENVELOPES, check_existing_detectors, choose_format, unavailable, validate_candidate_text,
)
from piece_v2_expression import (
    _DEPENDENT_START, _EMBEDDED_REPORT, _INTENT_ROLES, _REFERENCE,
    _SELF_TOPIC, _WISH_END,
)
from .contracts import EngineStatus, ExecutionMode
from .piece_source import (
    PiecePersonalEvaluation, PieceSourceMeaning, build_piece_source_meaning,
    piece_public_role_aliases, validate_piece_nominal_references,
    validate_piece_personal_evaluations, validate_piece_expression_scopes,
)


@dataclass(frozen=True, slots=True, repr=False)
class PieceGenerationRequest:
    request_id: str
    source: object
    expected_owner_id: str
    expected_saved_input_id: str
    expected_source_version: str
    tier: str = 'free'
    requested_format: str | None = None
    core_id: str = 'piece'
    product_job: str = 'EXPRESS_AND_SHARE'
    execution_mode: str = ExecutionMode.OFFLINE_CANDIDATE.value


@dataclass(frozen=True, slots=True)
class PieceArtifactIntent:
    product_job: str = 'EXPRESS_AND_SHARE'
    authorship: str = 'USER_OWNED_COCOLON_SHAPED'
    audience: str = 'EXTERNAL_SHARE_CARD_WITHIN_POLICY'
    publicization: str = 'SOURCE_STATED_ROLE_ABSTRACTION'


@dataclass(frozen=True, slots=True, repr=False)
class PieceTextDuty:
    node_id: str
    operation: str


@dataclass(frozen=True, slots=True, repr=False)
class PieceArtifactPlan:
    graph_id: str
    source_version: str
    intent: PieceArtifactIntent
    duties: tuple[PieceTextDuty, ...]
    block_node_ids: tuple[tuple[str, ...], ...]
    declaration_eligible: bool


@dataclass(frozen=True, slots=True, repr=False)
class PieceArtifact:
    body_blocks: tuple[str, ...]
    piece_text: str
    piece_text_hash: str
    format_type: str
    eligible_formats: tuple[str, ...]

    def content_payload(self) -> dict:
        return {'schema_version': 'piece.content_payload.v1',
                'format_type': self.format_type, 'body_blocks': list(self.body_blocks),
                'title': None, 'language': 'ja',
                'meaning_contract_version': 'piece.content_meaning.v1',
                'safety_contract_version': 'piece.public_safety_transformation.v1'}

    def as_candidate(self) -> dict:
        return {'candidate_state': 'OFFLINE_NOT_ACCEPTED',
                'content_payload': self.content_payload(), 'piece_text': self.piece_text,
                'piece_text_hash': self.piece_text_hash,
                'eligible_formats': list(self.eligible_formats), 'format_type': self.format_type,
                'production_enabled': False, 'record_effect': 0, 'quota_effect': 0}


@dataclass(frozen=True, slots=True, repr=False)
class PieceEngineOutcome:
    status: EngineStatus
    reason_codes: tuple[str, ...]
    source_meaning: PieceSourceMeaning | None = None
    artifact_plan: PieceArtifactPlan | None = None
    artifact: PieceArtifact | None = None
    automatic_progression: bool = False

    def as_body_free(self) -> dict:
        return {'core_id': 'piece', 'product_job': 'EXPRESS_AND_SHARE',
                'execution_mode': ExecutionMode.OFFLINE_CANDIDATE.value,
                'status': self.status.value, 'reason_codes': list(self.reason_codes),
                'artifact_present': self.artifact is not None,
                'automatic_progression': False, 'production_enabled': False,
                'record_effect': 0, 'quota_effect': 0}


def _focal_parts(sentence: str) -> tuple[str, str, str] | None:
    from piece_v2_generation import _FOCUS, _DEICTIC, _NESTED
    match = _FOCUS.fullmatch(sentence)
    if match is None:
        return None
    obj = match['object'].lstrip('、，,')
    if (not obj.endswith(('こと', 'もの', '時間'))
            or _NESTED.search(obj) or _DEICTIC.search(obj)):
        raise unavailable('focal_object_not_self_contained')
    return obj, match['predicate'], match['speaker']


def compile_piece_artifact_plan(meaning: PieceSourceMeaning) -> PieceArtifactPlan:
    """Keep every source proposition and its dependent qualification together.

    Shared roles may suggest an intent, but cannot supply its words, speaker,
    missing cause, certainty or relation. The actual first-person construction
    must also bind. Non-final intents no longer lose subsequent uncertainty.
    """
    from piece_v2_generation import _UNCERTAIN, _DEICTIC
    graph = meaning.graph
    validate_piece_nominal_references(meaning)
    validate_piece_personal_evaluations(meaning)
    evaluations = {frame.node_id: frame for frame in meaning.personal_evaluations}
    validate_piece_expression_scopes(meaning)
    scopes = {scope.node_id: scope for scope in meaning.expression_scopes}
    duties: list[PieceTextDuty] = []
    intents: list[int] = []
    focal = False
    for index, (node, semantic) in enumerate(zip(graph.nodes, meaning.sentences, strict=True)):
        sentence = node.value
        admitted = [r.reference_scalar_span for r in meaning.nominal_references
                    if r.reference_node_id == node.node_id]
        if _DEICTIC.search(sentence) or any(
                not any(a <= semantic.source_start + m.start()
                        and semantic.source_start + m.end() <= b for a, b in admitted)
                for m in _REFERENCE.finditer(sentence)):
            raise unavailable('unresolved_reference')
        if node.node_id in scopes:
            duties.append(PieceTextDuty(node.node_id, 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'))
            intents.append(index)
            continue
        if _focal_parts(sentence) is not None:
            duties.append(PieceTextDuty(node.node_id, 'SOURCE_FOCAL_TO_FIRST_PERSON'))
            intents.append(index)
            focal = True
            continue
        if node.node_id in evaluations:
            duties.append(PieceTextDuty(node.node_id, 'SOURCE_PERSONAL_EVALUATION'))
            intents.append(index)
            continue
        topic = _SELF_TOPIC.fullmatch(sentence)
        if (topic is not None and _WISH_END.search(topic['body'])
                and semantic.role in _INTENT_ROLES
                and not _DEPENDENT_START.search(topic['body'])
                and not _EMBEDDED_REPORT.search(topic['body'])):
            duties.append(PieceTextDuty(node.node_id, 'SOURCE_FIRST_PERSON_TOPIC'))
            intents.append(index)
        else:
            duties.append(PieceTextDuty(node.node_id, 'KEEP_COMPLETE_SOURCE_CONTEXT'))
    if not intents:
        raise unavailable('expression_meaning_not_admitted')
    ids = tuple(node.node_id for node in graph.nodes)
    dependent = any(_DEPENDENT_START.search(node.value) for node in graph.nodes)
    if meaning.nominal_references:
        # Antecedents, mentions and subsequent reservations remain a single
        # source-ordered reading group. No isolated quote, inferred expansion
        # or last-wish-first move can detach what the reference refers to.
        first = min(ids.index(r.antecedent_node_id) for r in meaning.nominal_references)
        blocks = (ids[:first], ids[first:]) if first else (ids,)
    elif evaluations or meaning.expression_scopes:
        # Keep each value, preference and source-marked reason/condition with
        # every qualification in source order; never excerpt a pledge.
        blocks = (ids,)
    elif focal:
        # Keep the existing admitted focal path's canonical block identity.
        blocks = tuple((node_id,) for node_id in ids) if len(ids) <= 3 else (
            (ids[0],), ids[1:-1], (ids[-1],))
    elif len(intents) == 1 and intents[0] == len(ids)-1 and len(ids) > 1 and not dependent:
        blocks = ((ids[-1],), ids[:-1])
    elif len(ids) == 1:
        blocks = (ids,)
    else:
        # A wish followed by a limitation is one reading group. Never move it
        # to the end, turn it into a standalone declaration, or drop its tail.
        pivot = intents[0]
        blocks = (ids[:pivot], ids[pivot:]) if pivot else (ids,)
    declaration = (len(ids) == 1 and not meaning.expression_scopes
                   and not _UNCERTAIN.search(graph.nodes[0].value))
    if evaluations:
        # A past preference, negation or tentative assessment is not a promise.
        # Only an explicit present value can additionally offer declaration.
        frame = evaluations.get(ids[0])
        declaration = bool(declaration and frame is not None
                           and frame.kind == 'PERSONAL_VALUE'
                           and frame.temporal_scope == 'NONPAST'
                           and frame.polarity == 'AFFIRMATIVE'
                           and frame.commitment == 'ASSERTED'
                           and not re.search(r'もし|なら|たら|とき|場合', graph.nodes[0].value))
    return PieceArtifactPlan(graph.graph_id, graph.source_version, PieceArtifactIntent(),
                             tuple(duties), blocks, declaration)


def _publicize_source_sentence(sentence: str, meaning: PieceSourceMeaning) -> str:
    # Replacements use source-written roles and explicitly bound named owners.
    # No generic mask, new social role or inferred person is introduced.
    source_text = meaning.envelope.raw_utf8.decode('utf-8')
    for binding in meaning.role_bindings:
        if source_text[binding.source_start:binding.source_end] != binding.role + 'の' + binding.name:
            raise unavailable('public_role_source_binding')
    aliases = piece_public_role_aliases(meaning.role_bindings)
    if not aliases:
        return sentence
    phrases = {b.role + 'の' + b.name: aliases[b.name] for b in meaning.role_bindings}
    # Consume the whole written phrase before a bare name. A single pass
    # prevents an inserted qualification from being replaced again, and
    # preserves a shorter explicit binding without duplicating its prefix.
    full = '|'.join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
    names = '|'.join(re.escape(n) for n in sorted(aliases, key=len, reverse=True))
    replacements = {**phrases, **aliases}
    return re.sub(full + r'|(?<![一-龥々])(?:' + names + ')',
                  lambda match: replacements[match.group()], sentence)


def _evaluation_sentence(meaning: PieceSourceMeaning, frame: PiecePersonalEvaluation) -> str:
    """One writer realization shared by free and explicitly scoped evaluations."""
    original = meaning.envelope.raw_utf8.decode('utf-8')
    speaker, predicate, target = (original[a:b] for a, b in frame.scalar_parts)
    perspective = speaker + ('にとって' if frame.construction == 'にとって' else 'は')
    # Only the relative nominal copula な becomes its source register's
    # finite copula. Negative/past/modal predicates stay byte-exact.
    finite = predicate[:-1] + frame.copula if predicate.endswith('な') else predicate
    return perspective + '、' + target + 'が' + finite + '。'


def _linked_self_continuations(meaning: PieceSourceMeaning,
                               plan: PieceArtifactPlan) -> frozenset[str]:
    """Reduce an adjacent, source-proven author repetition, not subject meaning.

    The same-block antecedent must itself state the same literal first person.
    A validated nominal reference must open the following written scope. Only
    its explicit wish may omit the redundant topic; an evaluation viewpoint,
    comparison, intervening context or different speaker is never elided.
    Source/graph/plan validators run before this editorial choice is consumed.
    """
    original = meaning.envelope.raw_utf8.decode('utf-8')
    nodes = {node.node_id: node for node in meaning.graph.nodes}
    evaluations = {frame.node_id: frame for frame in meaning.personal_evaluations}
    scopes = {scope.node_id: scope for scope in meaning.expression_scopes}
    references = {ref.reference_node_id: ref for ref in meaning.nominal_references}
    continuations = set()
    for group in plan.block_node_ids:
        for previous, current in zip(group, group[1:]):
            ref, scope = references.get(current), scopes.get(current)
            if (ref is None or scope is None or ref.antecedent_node_id != previous
                    or previous in scopes or current in evaluations
                    or ref.reference_scalar_span[0] != scope.scope_scalar_span[0]):
                continue
            # A linked referent does not establish the subject of its whole
            # scope. A later は/が/も can introduce another participant or a
            # contrast, so do not elide the author's explicit topic across it.
            # The referent's own initial は/が/も is not a competing subject.
            # Exclude the validated connective (including けれども) itself.
            # This conservative surface check only declines an optional edit;
            # it never rejects input or claims general subject resolution.
            tail = original[ref.reference_scalar_span[1]:
                            scope.scope_scalar_span[1] - len(scope.marker)]
            if re.search(r'[はがも]', tail[1:] if tail.startswith(('は', 'が', 'も')) else tail):
                continue
            topic = _SELF_TOPIC.fullmatch(original[slice(*scope.expression_scalar_span)])
            if topic is None or not _WISH_END.search(topic['body']):
                continue
            frame = evaluations.get(previous)
            focal = _focal_parts(nodes[previous].value) if frame is None else None
            speaker = (original[slice(*frame.scalar_parts[0])] if frame is not None
                       else focal[2] if focal is not None else None)
            if speaker == topic['speaker']:
                continuations.add(current)
    return frozenset(continuations)


def _adjacent_self_continuations(meaning: PieceSourceMeaning,
                                 plan: PieceArtifactPlan) -> frozenset[str]:
    """Find optional self-topic omissions from explicit, adjacent duties.

    Two wishes, or a focal/evaluative author followed by a bound plain-topic
    preference, can share a written author. Another subject/contrast, source
    line break, scoped duty or paragraph boundary keeps the topic. A preceding
    evaluation's viewpoint is retained; the following explicit viewpoint or
    focus is never elided. Both propositions must state the same first person.
    A continued preference may extend that same source-bound referent chain,
    but cannot start a new chain after an unlicensed link. The plan remains
    intact; this is not general subject/discourse resolution.
    """
    original = meaning.envelope.raw_utf8.decode('utf-8')
    nodes = {node.node_id: node for node in meaning.graph.nodes}
    positions = {node.node_id: i for i, node in enumerate(meaning.graph.nodes)}
    spans = {sentence.node_id: sentence for sentence in meaning.sentences}
    duties = {duty.node_id: duty.operation for duty in plan.duties}
    evaluations = {frame.node_id: frame for frame in meaning.personal_evaluations}
    continuations = set()
    continuation_referents = {}
    for group in plan.block_node_ids:
        for previous, current in zip(group, group[1:]):
            if positions[current] != positions[previous] + 1:
                continue
            gap = original[spans[previous].source_end:spans[current].source_start]
            if '\n' in gap or '\r' in gap:
                continue
            if (duties[previous] in {'SOURCE_FOCAL_TO_FIRST_PERSON',
                                     'SOURCE_PERSONAL_EVALUATION'}
                    and duties[current] == 'SOURCE_PERSONAL_EVALUATION'):
                prior = evaluations.get(previous)
                if duties[previous] == 'SOURCE_PERSONAL_EVALUATION':
                    # An existing source-bound evaluation can establish this
                    # author and referent. Keep its full viewpoint/predicate;
                    # no new source admission or evaluation inference occurs.
                    if prior is None or prior.construction not in {'は', 'にとって'}:
                        continue
                    speaker = original[slice(*prior.scalar_parts[0])]
                    target = original[slice(*prior.scalar_parts[2])]
                else:
                    focal = _focal_parts(nodes[previous].value)
                    if focal is None:
                        continue
                    target, _, speaker = focal
                frame = evaluations.get(current)
                # Only the next plain は preference can omit its self-topic.
                # Its explicit にとって viewpoint, が focus or comparison stays.
                if (frame is None or frame.construction != 'は'
                        or frame.kind != 'PERSONAL_PREFERENCE'
                        or original[slice(*frame.scalar_parts[0])] != speaker):
                    continue
                links = [ref for ref in meaning.nominal_references
                         if ref.reference_node_id == current
                         and ref.reference_scalar_span == frame.scalar_parts[2]
                         and ref.reference_utf8_span == frame.utf8_parts[2]]
                if len(links) != 1:
                    continue
                ref = links[0]
                referent = (ref.antecedent_node_id, ref.nominal_head,
                            ref.antecedent_scalar_span, ref.antecedent_utf8_span)
                # The resolver keeps later mentions bound to the original
                # object, not the preceding pronoun. Extend only a previously
                # licensed adjacent continuation of that exact source object.
                # Matching visible words, proximity, or an earlier standalone
                # mention cannot restart a chain across a declined boundary.
                if continuation_referents.get(previous) == referent:
                    # Do not manufacture identical adjacent sentences. Keep
                    # the source's repeated proposition and its explicit topic,
                    # just as the existing two-wish edit declines duplicates.
                    if (prior is None or _evaluation_sentence(meaning, prior)
                            == _evaluation_sentence(meaning, frame)):
                        continue
                    continuations.add(current)
                    continuation_referents[current] = referent
                    continue
                if (ref.antecedent_node_id != previous
                        or original[slice(*links[0].antecedent_scalar_span)] != target
                        or (prior is not None and (
                            links[0].antecedent_scalar_span != prior.scalar_parts[2]
                            or links[0].antecedent_utf8_span != prior.utf8_parts[2]))
                        # The bound head もの contains も, not a contrast particle.
                        or re.search(r'[はがも]', target[:-len(links[0].nominal_head)])):
                    continue
                continuations.add(current)
                continuation_referents[current] = referent
                continue
            if (duties[previous] != 'SOURCE_FIRST_PERSON_TOPIC'
                    or duties[current] != 'SOURCE_FIRST_PERSON_TOPIC'):
                continue
            before = _SELF_TOPIC.fullmatch(nodes[previous].value)
            after = _SELF_TOPIC.fullmatch(nodes[current].value)
            if (before is None or after is None
                    or before['speaker'] != after['speaker']
                    or before['body'] == after['body']):
                continue
            # Do not move an implicit subject across another participant or
            # contrast. Even lexical false positives only decline this optional
            # edit; they do not make an otherwise admitted input unavailable.
            if any(re.search(r'[はがも]', topic['body']) for topic in (before, after)):
                continue
            continuations.add(current)
    return frozenset(continuations)


def realize_piece_artifact(meaning: PieceSourceMeaning, plan: PieceArtifactPlan,
                           *, tier: str, requested_format: str | None) -> PieceArtifact:
    """Realize plan-owned duties from the source graph; never call B8's old author."""
    graph = meaning.graph
    if plan.graph_id != graph.graph_id or plan.source_version != graph.source_version:
        raise unavailable('piece_plan_source_binding')
    ids = tuple(node.node_id for node in graph.nodes)
    ordered = tuple(node_id for block in plan.block_node_ids for node_id in block)
    if (tuple(d.node_id for d in plan.duties) != ids
            or sorted(ordered) != sorted(ids) or len(ordered) != len(ids)
            or any(not block for block in plan.block_node_ids)):
        raise unavailable('piece_plan_complete_coverage')
    if plan.intent != PieceArtifactIntent():
        raise unavailable('piece_intent_mismatch')
    if plan != compile_piece_artifact_plan(meaning):
        raise unavailable('piece_plan_semantic_binding')
    continuations = _linked_self_continuations(meaning, plan)
    sentences: dict[str, str] = {}
    for node, duty, evidence in zip(graph.nodes, plan.duties, meaning.evidence, strict=True):
        raw = meaning.envelope.raw_utf8
        if (node.evidence_ids != (evidence.evidence_id,)
                or raw[evidence.utf8_start:evidence.utf8_end].decode('utf-8') != node.value):
            raise unavailable('piece_graph_source_binding')
        text = _publicize_source_sentence(node.value, meaning)
        if duty.operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON':
            scope = next((s for s in meaning.expression_scopes if s.node_id == node.node_id), None)
            if scope is None:
                raise unavailable('piece_plan_operation_binding')
            original = raw.decode('utf-8')
            premise = original[slice(*scope.scope_scalar_span)]
            frame = next((f for f in meaning.personal_evaluations if f.node_id == node.node_id), None)
            if frame is not None:
                # The condition/reason governs this evaluation. Keep it before
                # the complete first-person evaluation, rather than outputting
                # a free-standing value or manufacturing a wish from liking.
                text = _publicize_source_sentence(
                    premise + '、' + _evaluation_sentence(meaning, frame), meaning)
            else:
                topic = _SELF_TOPIC.fullmatch(original[slice(*scope.expression_scalar_span)])
                if topic is None:
                    raise unavailable('piece_plan_operation_binding')
                # Realize the written first-person topic. The complete premise,
                # its exact connective, and all intention arguments stay intact.
                # In particular なら never becomes ので, and neither clause is
                # changed into a new causal explanation or an unconditional vow.
                # An adjacent source-bound continuation already establishes
                # this author. Keep its full scope and predicate; omit only
                # the repeated self-topic, never the first visible viewpoint.
                prefix = '' if node.node_id in continuations else topic['speaker'] + 'は、'
                referenced_premise = any(
                    ref.reference_node_id == node.node_id
                    and scope.scope_scalar_span[0] <= ref.reference_scalar_span[0]
                    and ref.reference_scalar_span[1] <= scope.scope_scalar_span[1]
                    for ref in meaning.nominal_references)
                if (scope.relation == 'SOURCE_EXPLICIT_CONCESSION'
                        or referenced_premise):
                    # Keep the source-bound premise before the written topic.
                    # A nominal link does not make its participant the author;
                    # fronting a retained topic can blur that clause boundary.
                    # The existing continuation check alone owns omission.
                    text = premise + '、' + prefix + topic['body'] + '。'
                else:
                    text = prefix + premise + '、' + topic['body'] + '。'
                text = _publicize_source_sentence(text, meaning)
        elif duty.operation == 'SOURCE_FOCAL_TO_FIRST_PERSON':
            parts = _focal_parts(text)
            if parts is None:
                raise unavailable('piece_plan_operation_binding')
            obj, predicate, speaker = parts
            text = speaker + 'は、' + obj + 'を' + predicate + '。'
        elif duty.operation == 'SOURCE_FIRST_PERSON_TOPIC':
            topic = _SELF_TOPIC.fullmatch(text)
            if topic is None or not _WISH_END.search(topic['body']):
                raise unavailable('piece_plan_operation_binding')
            text = topic['speaker'] + 'は、' + topic['body'] + '。'
        elif duty.operation == 'SOURCE_PERSONAL_EVALUATION':
            frame = next((f for f in meaning.personal_evaluations if f.node_id == node.node_id), None)
            if frame is None:
                raise unavailable('piece_plan_operation_binding')
            text = _publicize_source_sentence(_evaluation_sentence(meaning, frame), meaning)
        elif duty.operation != 'KEEP_COMPLETE_SOURCE_CONTEXT':
            raise unavailable('piece_plan_operation_unknown')
        sentences[node.node_id] = text
    # Apply the optional continuity edit only after source/plan validation and
    # complete realization. Remove just the redundant topic, not a proposition,
    # public relationship, predicate, negation, reservation or the first author.
    adjacent = _adjacent_self_continuations(meaning, plan)
    if adjacent:
        edited = dict(sentences)
        for node_id in adjacent:
            topic = _SELF_TOPIC.fullmatch(edited[node_id])
            if topic is None:
                raise unavailable('piece_plan_operation_binding')
            edited[node_id] = topic['body'] + '。'
        # These multisentence bodies are short essays. An optional edit must not turn
        # an admitted short essay into a below-minimum refusal. Decline the edit
        # rather than changing the existing envelope or padding the user's text.
        length = len(re.sub(r'\s', '', ''.join(edited.values())))
        if length >= ENVELOPES['short_essay'][0]:
            sentences = edited
    blocks = tuple(''.join(sentences[node_id] for node_id in group)
                   for group in plan.block_node_ids)
    payloads = {}
    for fmt in ('short_essay', 'quote', 'declaration'):
        if fmt == 'quote' and (len(ids) != 1 or meaning.expression_scopes):
            continue
        if fmt == 'declaration' and not plan.declaration_eligible:
            continue
        payload = {'schema_version': 'piece.content_payload.v1', 'format_type': fmt,
                   'body_blocks': list(blocks), 'title': None, 'language': 'ja',
                   'meaning_contract_version': 'piece.content_meaning.v1',
                   'safety_contract_version': 'piece.public_safety_transformation.v1'}
        try:
            validate_candidate_text(payload)
        except ValueError:
            # Existing content-envelope owner exposes ValueError; the legacy
            # B01 loader may also reload its concrete exception class.
            continue
        payloads[fmt] = payload
    eligible = tuple(payloads)
    recommended = 'declaration' if 'declaration' in eligible else (
        'quote' if 'quote' in eligible else 'short_essay')
    selected = choose_format(tier=tier, requested=requested_format,
                             eligible=eligible, recommended=recommended)
    text = validate_candidate_text(payloads[selected])
    check_existing_detectors(text)
    return PieceArtifact(blocks, text, hashlib.sha256(text.encode('utf-8')).hexdigest(),
                         selected, eligible)


def generate_piece_artifact(request: PieceGenerationRequest) -> PieceEngineOutcome:
    if (type(request) is not PieceGenerationRequest or request.core_id != 'piece'
            or request.product_job != 'EXPRESS_AND_SHARE'
            or request.execution_mode != ExecutionMode.OFFLINE_CANDIDATE.value
            or not isinstance(request.request_id, str) or not request.request_id.strip()):
        return PieceEngineOutcome(EngineStatus.REJECTED, ('piece_request_out_of_scope',))
    meaning = None
    plan = None
    try:
        meaning = build_piece_source_meaning(
            request.source, expected_owner_id=request.expected_owner_id,
            expected_saved_input_id=request.expected_saved_input_id,
            expected_source_version=request.expected_source_version)
        plan = compile_piece_artifact_plan(meaning)
        artifact = realize_piece_artifact(meaning, plan, tier=request.tier,
                                          requested_format=request.requested_format)
    except PieceContractError as exc:
        return PieceEngineOutcome(EngineStatus.UNAVAILABLE, (exc.detail or 'piece_content_unavailable',),
                                  meaning, plan)
    except Exception:
        # Private source/graph exceptions are never copied into an outcome.
        return PieceEngineOutcome(EngineStatus.UNAVAILABLE, ('piece_vertical_internal_failure',))
    return PieceEngineOutcome(EngineStatus.GENERATED, ('piece_source_plan_generated',),
                              meaning, plan, artifact)
