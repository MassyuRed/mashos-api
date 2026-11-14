"""Bounded private refined Piece: two qualified sources, the existing author.

This slice composes an original and one explicitly opted-in real answer.
Saved-source admission owns the shared one-round update proof; this module
keeps its active complete-clause ranges without resolving a new target or
rewriting either source. It does not authenticate a caller or issue a preview.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
import base64
import hashlib
import json
import re

from piece_v2_content_policy import (
    check_existing_detectors, choose_format, unavailable,
    validate_candidate_text, validate_source_meaning_preservation,
)
from piece_v2_contract import canonical_json_bytes
from .contracts import EngineStatus
from .emlis_thread_contracts import SupplementalAnswerSource
from .emlis_thread_source import FrozenSupplementalAnswer, freeze_supplemental_answer
from .piece_source import PieceSourceMeaning, build_piece_source_meaning


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedSourceSnapshot:
    original: object
    supplemental: SupplementalAnswerSource
    supplemental_owner_id: str
    question_need_decision_identity: str
    refined_result_identity: str
    original_commitment: str
    supplemental_commitment: str
    opted_in: bool
    supplemental_update_operation: str
    # Populated only by the saved one-round answer-update owner. These are
    # exact scalar ranges of the unchanged original fields and real answer.
    original_active_ranges: tuple[tuple[str, int, int], ...] = ()
    supplemental_active_range: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True, repr=False)
class PieceSupplementalMeaning(PieceSourceMeaning):
    # A real answer envelope, never an original-input identity. Local grammar
    # coordinates address answer_text_private; UTF-8 evidence addresses this
    # metadata-framed envelope from the existing answer-source owner.
    frozen_answer: FrozenSupplementalAnswer | None = None
    grammar_owner_id: str = ''
    active_range: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True, repr=False)
class PieceActiveOriginalMeaning(PieceSourceMeaning):
    active_ranges: tuple[tuple[str, int, int], ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedMeaning:
    source: PieceRefinedSourceSnapshot
    source_ref: str
    original: PieceSourceMeaning
    supplemental: PieceSupplementalMeaning | None


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedPlan:
    source_ref: str
    original_plan: object
    supplemental_plan: object
    # No relation is invented across sources. Preserve the original blocks,
    # then the answer blocks, with explicit source boundaries in private state.
    source_roles: tuple[str, str] = ('ORIGINAL_USER_INPUT', 'SUPPLEMENTAL_ANSWER')
    eligible_formats: tuple[str, ...] = ('short_essay',)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require(value, code='piece_refined_source_binding'):
    if not value:
        raise unavailable(code)


def _source_payload(source):
    from piece_v2_generation import PieceSourceSnapshot
    _require(type(source) is PieceRefinedSourceSnapshot)
    _require(type(source.original) is PieceSourceSnapshot)
    original = asdict(source.original)
    raw = original.pop('saved_original_json')
    _require(type(raw) is bytes)
    original['saved_original_base64'] = base64.b64encode(raw).decode('ascii')
    result = asdict(source)
    result['original'] = original
    # Existing ADD source identities and private saved bytes remain exact.
    if not source.original_active_ranges and source.supplemental_active_range is None:
        del result['original_active_ranges']
        del result['supplemental_active_range']
    if source.original_active_ranges:
        result['original_active_ranges'] = [list(row) for row in source.original_active_ranges]
    if source.supplemental_active_range is not None:
        result['supplemental_active_range'] = list(source.supplemental_active_range)
    return result


def refined_source_ref(source) -> str:
    return 'piece-refined:' + _sha(canonical_json_bytes(_source_payload(source)))


def _supplemental_meaning(answer, owner_id, active_range=None):
    """Adapt existing finite grammar, then bind every node to its answer source.

    The temporary text view is only a parser input. It is not retained as
    semantic source or saved original, nor joined to the actual original.
    The returned graph and all evidence use the answer owner's real envelope.
    """
    from piece_v2_generation import PieceSourceSnapshot
    from .source_kernel import _evidence_id
    frozen = freeze_supplemental_answer(answer)
    raw = answer.answer_text_private
    start, end = (0, len(raw)) if active_range is None else active_range
    _require(type(start) is int and type(end) is int and 0 <= start < end <= len(raw))
    literal = raw[start:end]
    # A source-bound complete SELF replacement can end at its closing quote.
    # The stop below is grammar-only. It never enters the node/evidence/raw
    # source and does not supply an omitted predicate or narrator.
    grammar_stop = active_range is not None and literal[-1] not in '。！？!?'
    if grammar_stop:
        from .piece_source import _qualified_self_topic, _literal_self_account
        _require(_qualified_self_topic(literal + '。') is not None
                 and _literal_self_account(literal + '。'), 'piece_refined_replacement_not_self_contained')
    view = PieceSourceSnapshot(owner_id, answer.answer_id, answer.source_version,
                               literal + ('。' if grammar_stop else ''))
    parsed = build_piece_source_meaning(view, expected_owner_id=owner_id,
        expected_saved_input_id=answer.answer_id, expected_source_version=answer.source_version)
    _require(bool(frozen.evidence_refs))
    if active_range is not None:
        _require(len(parsed.graph.nodes) == 1 and not parsed.role_bindings
            and not parsed.nominal_references and not parsed.personal_evaluations
            and not parsed.expression_scopes, 'piece_refined_replacement_not_self_contained')
    field = frozen.evidence_refs[0]
    evidence = []
    ids = {}
    for local in parsed.evidence:
        local_end = min(local.scalar_end, len(literal))
        quote = literal[local.scalar_start:local_end]
        values = dict(source_span_id=local.source_span_id, field_path=field.field_path,
            element_index=field.element_index, field_utf8_start=field.field_utf8_start,
            field_utf8_end=field.field_utf8_end, scalar_start=start + local.scalar_start,
            scalar_end=start + local_end,
            utf8_start=field.field_utf8_start + len(raw[:start + local.scalar_start].encode('utf-8')),
            utf8_end=field.field_utf8_start + len(raw[:start + local_end].encode('utf-8')),
            field_sha256=field.field_sha256, literal_sha256=_sha(quote.encode('utf-8')))
        eid = _evidence_id(envelope_id=frozen.envelope.envelope_id, **values)
        ids[local.evidence_id] = eid
        evidence.append(replace(local, evidence_id=eid,
            source_envelope_id=frozen.envelope.envelope_id, **values))
    graph = replace(parsed.graph,
        graph_id='piece-graph:' + _sha(canonical_json_bytes(
            [frozen.envelope.envelope_id, parsed.graph.graph_id] if active_range is None else
            [frozen.envelope.envelope_id, parsed.graph.graph_id, list(active_range)])),
        source_envelope_id=frozen.envelope.envelope_id,
        nodes=tuple(replace(n, value=literal if grammar_stop else n.value,
                            evidence_ids=tuple(ids[e] for e in n.evidence_ids))
                    for n in parsed.graph.nodes),
        edges=tuple(replace(e, evidence_ids=tuple(ids[r] for r in e.evidence_ids))
                    for e in parsed.graph.edges),
        owner_dispositions=tuple(replace(o, evidence_refs=tuple(ids[e] for e in o.evidence_refs))
                                 for o in parsed.graph.owner_dispositions))
    values = {f.name: getattr(parsed, f.name) for f in fields(PieceSourceMeaning)}
    values.update(envelope=frozen.envelope, graph=graph, evidence=tuple(evidence),
        sentences=tuple(replace(s, evidence_id=ids[s.evidence_id],
            source_start=start + s.source_start, source_end=start + min(s.source_end, len(literal)))
            for s in parsed.sentences))
    return PieceSupplementalMeaning(**values, frozen_answer=frozen, grammar_owner_id=owner_id,
                                    active_range=active_range)


def validate_supplemental_meaning(meaning):
    _require(type(meaning) is PieceSupplementalMeaning
             and type(meaning.frozen_answer) is FrozenSupplementalAnswer)
    # Re-derive parser/evidence only, never the author. Saved re-read below
    # does not enter this function; this is generation-time source validation.
    _require(type(meaning.grammar_owner_id) is str and bool(meaning.grammar_owner_id.strip()))
    expected = _supplemental_meaning(meaning.frozen_answer.source, meaning.grammar_owner_id, meaning.active_range)
    # The grammar's local owner is not part of its graph/source identity.
    _require(meaning == expected, 'piece_refined_answer_evidence_binding')



def _active_original_meaning(source, ranges):
    """Keep complete surviving nodes at their original field/envelope offsets.

    Saved-source admission supplies the shared Emlis update proof. This view
    does not infer a target, splice an envelope or connect across a removal.
    """
    from .piece_source import (piece_text_nodes, _qualified_self_topic,
                               _selected_feeling_bindings)
    full = build_piece_source_meaning(source, expected_owner_id=source.owner_id,
        expected_saved_input_id=source.saved_input_id, expected_source_version=source.source_version)
    _require(type(ranges) is tuple and bool(ranges), 'piece_refined_active_range_binding')
    by_range = {(ref.field_path, ref.scalar_start, ref.scalar_end): ref for ref in full.evidence}
    _require(all(type(item) is tuple and len(item) == 3
        and type(item[0]) is str and type(item[1]) is int and type(item[2]) is int
        and item in by_range for item in ranges)
        and len(set(ranges)) == len(ranges), 'piece_refined_active_range_binding')
    chosen = {by_range[item].source_span_id for item in ranges}
    nodes = tuple(node for node in piece_text_nodes(full) if node.node_id in chosen)
    evidence = tuple(ref for ref in full.evidence if ref.source_span_id in chosen)
    _require(tuple((ref.field_path, ref.scalar_start, ref.scalar_end) for ref in evidence) == ranges,
             'piece_refined_active_range_binding')
    removed = tuple(node for node in piece_text_nodes(full) if node.node_id not in chosen)
    _require(len(removed) == 1 and _qualified_self_topic(removed[0].value) is not None,
             'piece_refined_update_not_supported')
    # An antecedent or its dependent may not be silently reattached after
    # removal. Within-node conditions/evaluations survive only in full.
    _require(not full.role_bindings
        and not any(row.node_id == removed[0].node_id
                    for row in (*full.expression_scopes, *full.personal_evaluations))
        and not any(removed[0].node_id in
        (ref.antecedent_node_id, ref.reference_node_id) for ref in full.nominal_references),
        'piece_refined_update_dependency_not_supported')
    sentences = tuple(row for row in full.sentences if row.node_id in chosen)
    edges = tuple(row for row in full.graph.edges
                  if row.source_node_id in chosen and row.target_node_id in chosen)
    owners = tuple(node.owner_id for node in nodes)
    graph = replace(full.graph,
        graph_id='piece-graph:' + _sha(canonical_json_bytes([full.graph.graph_id, [list(row) for row in ranges]])),
        nodes=nodes, edges=edges,
        owner_dispositions=tuple(row for row in full.graph.owner_dispositions
                                 if row.meaning_owner_id in owners),
        required_owner_refs=owners,
        owner_universe_digest=_sha(json.dumps(owners).encode()))
    selected, selection_evidence, selection_contexts = _selected_feeling_bindings(source, nodes, evidence)
    values = {field.name: getattr(full, field.name) for field in fields(PieceSourceMeaning)}
    values.update(graph=graph, evidence=evidence, sentences=sentences,
        nominal_references=tuple(row for row in full.nominal_references
            if row.antecedent_node_id in chosen and row.reference_node_id in chosen),
        personal_evaluations=tuple(row for row in full.personal_evaluations if row.node_id in chosen),
        expression_scopes=tuple(row for row in full.expression_scopes if row.node_id in chosen),
        selected_feelings=selected, selection_evidence=selection_evidence,
        selection_contexts=selection_contexts)
    return PieceActiveOriginalMeaning(**values, active_ranges=ranges)


def validate_active_original_meaning(meaning):
    _require(type(meaning) is PieceActiveOriginalMeaning
             and meaning == _active_original_meaning(meaning.saved_snapshot, meaning.active_ranges),
             'piece_refined_active_range_binding')


def supplemental_statement_view(meaning, node):
    """A grammar-only terminator for one already qualified replacement."""
    if (type(meaning) is PieceSupplementalMeaning and meaning.active_range is not None
            and node in meaning.graph.nodes and not node.value.endswith(tuple('。！？!?'))):
        return node.value + '。'
    return node.value


def supplemental_complete_self_account(meaning):
    from .piece_source import _qualified_self_topic, _literal_self_account
    return (type(meaning) is PieceSupplementalMeaning and meaning.active_range is not None
        and len(meaning.graph.nodes) == 1 and all(
            _qualified_self_topic(supplemental_statement_view(meaning, node)) is not None
            and _literal_self_account(supplemental_statement_view(meaning, node))
            for node in meaning.graph.nodes))


def refined_meaning_parts(meaning, plan):
    parts = ((meaning.original, plan.original_plan),)
    if meaning.supplemental is not None:
        _require(plan.supplemental_plan is not None, 'piece_refined_plan_binding')
        parts += ((meaning.supplemental, plan.supplemental_plan),)
    else:
        _require(plan.supplemental_plan is None and meaning.source.supplemental_update_operation == 'WITHDRAW',
                 'piece_refined_plan_binding')
    return parts


def _supplemental_feeling_prefix_end(text):
    """Read a complete SELF feeling without changing its written time.

    The answer owner's NOW/THEN grammar supplies only a parse boundary. The
    original relative-time words remain in the proposition and its evidence;
    neither the original's recorded date nor its selected feeling fills them.
    """
    from piece_v2_expression import _SELF_TOPIC
    from .emlis_answer_update import _FEELING, _NOW, _THEN
    from .piece_source import _written_feeling_expression
    if type(text) is not str or not text.endswith('。'):
        return None
    prefix = _NOW.match(text) or _THEN.match(text)
    end = prefix.end() if prefix is not None else 0
    body = text[end:]
    topic = _SELF_TOPIC.fullmatch(body)
    if topic is None or not (
            _FEELING.fullmatch('私は' + topic['body'])
            or _written_feeling_expression(body, current_affirmative_only=False) is not None):
        return None
    return end


def supplemental_feeling_time_span(meaning, node):
    """Locate only a fully read answer feeling's written THEN prefix.

    This is a local temporal-token exemption, not a nominal-reference
    resolver. Other source types and references elsewhere remain unchanged.
    """
    from .emlis_answer_update import _THEN
    if type(meaning) is not PieceSupplementalMeaning or node not in meaning.graph.nodes:
        return None
    prefix = _THEN.match(node.value)
    end = _supplemental_feeling_prefix_end(node.value)
    return (0, end) if prefix is not None and end == prefix.end() else None


def supplemental_feeling_account(meaning):
    """Keep a complete explicit SELF feeling from its own answer field.

    The optional source-written NOW/THEN prefix stays in the unchanged KEEP
    proposition. It is never resolved to an absolute date or removed.
    """
    if type(meaning) is not PieceSupplementalMeaning or not meaning.graph.nodes:
        return False
    for node in meaning.graph.nodes:
        if _supplemental_feeling_prefix_end(node.value) is None:
            return False
    return True


def build_refined_meaning(request):
    from piece_v2_generation import PieceSourceSnapshot
    source = request.source
    _require(type(source) is PieceRefinedSourceSnapshot)
    original, answer = source.original, source.supplemental
    _require(type(original) is PieceSourceSnapshot and type(answer) is SupplementalAnswerSource)
    _require(source.opted_in is True, 'piece_refined_opt_in_required')
    _require(source.supplemental_update_operation in {'ADD', 'REVISE', 'WITHDRAW'}, 'piece_refined_update_not_supported')
    _require(source.supplemental_owner_id == original.owner_id == request.expected_owner_id,
             'piece_refined_owner_mismatch')
    # Event identity and the logical question_id are distinct in saved Q2.
    # Their actual pairing is established by the saved-source adapter; this
    # pure constructor does not authenticate fabricated private snapshots.
    _require(type(source.question_need_decision_identity) is str
        and bool(source.question_need_decision_identity.strip()),
        'piece_refined_question_binding')
    _require(type(source.refined_result_identity) is str and bool(source.refined_result_identity.strip()))
    _require(type(answer.round_index) is int and 1 <= answer.round_index <= 3
             and answer.answer_id != original.saved_input_id,
             'piece_refined_answer_binding')
    _require(type(original.saved_original_json) is bytes,
             'piece_refined_saved_original_required')
    _require(source.original_commitment == 'sha256:' + _sha(original.saved_original_json),
             'piece_refined_original_commitment')
    frozen = freeze_supplemental_answer(answer)
    _require(source.supplemental_commitment == 'sha256:' + frozen.envelope.raw_sha256
        and source.original_commitment != source.supplemental_commitment,
        'piece_refined_answer_commitment')
    if source.supplemental_update_operation == 'ADD':
        _require(not source.original_active_ranges and source.supplemental_active_range is None,
                 'piece_refined_active_range_binding')
        _require(not re.search(r'訂正|撤回|ではなく|じゃなく|違います|違った', answer.answer_text_private),
                 'piece_refined_update_not_supported')
        original_meaning = build_piece_source_meaning(original,
            expected_owner_id=request.expected_owner_id,
            expected_saved_input_id=request.expected_saved_input_id,
            expected_source_version=request.expected_source_version)
        supplemental = _supplemental_meaning(answer, original.owner_id)
    else:
        _require(answer.round_index == 1, 'piece_refined_update_not_supported')
        original_meaning = _active_original_meaning(original, source.original_active_ranges)
        if source.supplemental_update_operation == 'REVISE':
            _require(type(source.supplemental_active_range) is tuple
                     and len(source.supplemental_active_range) == 2,
                     'piece_refined_active_range_binding')
            supplemental = _supplemental_meaning(answer, original.owner_id, source.supplemental_active_range)
        else:
            _require(source.supplemental_active_range is None, 'piece_refined_active_range_binding')
            supplemental = None
    if supplemental is not None:
        _require(all(re.match(r'^(?:(?:以前|当時|今|現在|これから)[はも][、，,]\s*)?'
                             r'(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が|にとって)', n.value)
                     or supplemental_feeling_time_span(supplemental, n) is not None
                     for n in supplemental.graph.nodes), 'piece_refined_answer_not_self_contained')
    return PieceRefinedMeaning(source, refined_source_ref(source), original_meaning, supplemental)


def _plans(meaning):
    from .piece_v1c import compile_piece_artifact_plan
    return PieceRefinedPlan(meaning.source_ref, compile_piece_artifact_plan(meaning.original),
                             compile_piece_artifact_plan(meaning.supplemental) if meaning.supplemental is not None else None)


def validate_refined_preservation(meaning, plan, artifact):
    from .piece_v1c import PieceArtifact, PieceGenerationRequest
    _require(type(meaning) is PieceRefinedMeaning and type(plan) is PieceRefinedPlan
        and type(artifact) is PieceArtifact and plan.source_ref == meaning.source_ref
        and meaning.source_ref == refined_source_ref(meaning.source)
        and plan.source_roles == ('ORIGINAL_USER_INPUT', 'SUPPLEMENTAL_ANSWER')
        and plan.eligible_formats == ('short_essay',), 'piece_refined_artifact_binding')
    source = meaning.source.original
    expected = build_refined_meaning(PieceGenerationRequest(
        'piece-refined-review', meaning.source, source.owner_id,
        source.saved_input_id, source.source_version))
    _require(meaning == expected, 'piece_refined_artifact_source_binding')
    validate_candidate_text(artifact.content_payload())
    _require(artifact.format_type == 'short_essay' and artifact.eligible_formats == ('short_essay',)
        and artifact.piece_text == '\n\n'.join(artifact.body_blocks)
        and artifact.piece_text_hash == _sha(artifact.piece_text.encode()),
        'piece_refined_artifact_binding')
    count = len(plan.original_plan.block_node_ids)
    extra = len(plan.supplemental_plan.block_node_ids) if plan.supplemental_plan is not None else 0
    _require(len(artifact.body_blocks) == count + extra,
             'piece_refined_artifact_binding')
    offset = 0
    for part, child_plan in refined_meaning_parts(meaning, plan):
        blocks = artifact.body_blocks[offset:offset + len(child_plan.block_node_ids)]
        offset += len(blocks)
        text = '\n\n'.join(blocks)
        child = PieceArtifact(blocks, text, _sha(text.encode()), 'short_essay', ('short_essay',))
        validate_source_meaning_preservation(part, child_plan, child)
    check_existing_detectors(artifact.piece_text)


def realize_refined_piece_artifact(meaning, plan, *, tier, requested_format):
    """Use the sole Piece author for each qualified partition, in order."""
    from .piece_v1c import PieceArtifact, realize_piece_artifact
    _require(plan == _plans(meaning), 'piece_refined_plan_binding')
    choose_format(tier=tier, requested=requested_format,
                  eligible=('short_essay',), recommended='short_essay')
    parts = tuple(realize_piece_artifact(part, child, tier='free', requested_format=None)
        for part, child in refined_meaning_parts(meaning, plan))
    blocks = tuple(b for p in parts for b in p.body_blocks)
    text = '\n\n'.join(blocks)
    artifact = PieceArtifact(blocks, text, _sha(text.encode()), 'short_essay', ('short_essay',))
    validate_refined_preservation(meaning, plan, artifact)
    return artifact


def generate_refined_piece(request):
    from .piece_v1c import PieceEngineOutcome
    from piece_v2_contract import PieceContractError
    meaning = plan = None
    try:
        meaning = build_refined_meaning(request)
        plan = _plans(meaning)
        # Both partitions use the unchanged sole author. There is no author
        # for inferred bridges, no raw-text append and no generated Emlis text.
        artifact = realize_refined_piece_artifact(meaning, plan, tier=request.tier,
                                                  requested_format=request.requested_format)
        return PieceEngineOutcome(EngineStatus.GENERATED, ('piece_refined_source_plan_generated',),
                                   meaning, plan, artifact)
    except PieceContractError as exc:
        return PieceEngineOutcome(EngineStatus.UNAVAILABLE, (exc.detail or 'piece_refined_unavailable',),
                                   meaning, plan)
    except Exception:
        return PieceEngineOutcome(EngineStatus.UNAVAILABLE, ('piece_refined_internal_failure',))


def serialize_refined_piece(outcome):
    _require(outcome.status == EngineStatus.GENERATED and outcome.artifact is not None)
    validate_refined_preservation(outcome.source_meaning, outcome.artifact_plan, outcome.artifact)
    state = dict(schema_version='piece.refined_private_saved.v1',
        source_ref=outcome.source_meaning.source_ref,
        sources=_source_payload(outcome.source_meaning.source),
        plan=asdict(outcome.artifact_plan), artifact=asdict(outcome.artifact))
    # Private dataclass tuples become JSON arrays; the existing canonical
    # contract deliberately rejects Python tuples as public request values.
    return canonical_json_bytes(json.loads(json.dumps(state, ensure_ascii=False, allow_nan=False)))


def read_saved_refined_artifact(raw, *, expected_state_sha256):
    """Read exact saved bytes; expected digest belongs to the trusted store.

    This is private file persistence, not Piece SQL/preview authority. No
    parser, source reader, compiler, author, Engine or model runs on re-read.
    """
    from .piece_v1c import PieceArtifact
    _require(type(raw) is bytes and _sha(raw) == expected_state_sha256,
             'piece_refined_saved_integrity')
    try:
        row = json.loads(raw)
        _require(row['schema_version'] == 'piece.refined_private_saved.v1')
        a = row['artifact']
        artifact = PieceArtifact(tuple(a['body_blocks']), a['piece_text'], a['piece_text_hash'],
                                 a['format_type'], tuple(a['eligible_formats']))
        validate_candidate_text(artifact.content_payload())
        _require(artifact.piece_text == '\n\n'.join(artifact.body_blocks)
            and artifact.piece_text_hash == _sha(artifact.piece_text.encode()))
        return artifact
    except (ValueError, KeyError, TypeError):
        raise unavailable('piece_refined_saved_integrity') from None
