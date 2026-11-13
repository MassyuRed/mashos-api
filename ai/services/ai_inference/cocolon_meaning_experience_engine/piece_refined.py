"""Bounded private refined Piece: two qualified sources, the existing author.

This offline slice composes an original and one explicitly opted-in ADD answer.
It does not resolve corrections, cross-source references, authenticate a caller,
issue a public preview or replace the original-only application contract.
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


@dataclass(frozen=True, slots=True, repr=False)
class PieceSupplementalMeaning(PieceSourceMeaning):
    # A real answer envelope, never an original-input identity. Local grammar
    # coordinates address answer_text_private; UTF-8 evidence addresses this
    # metadata-framed envelope from the existing answer-source owner.
    frozen_answer: FrozenSupplementalAnswer | None = None
    grammar_owner_id: str = ''


@dataclass(frozen=True, slots=True, repr=False)
class PieceRefinedMeaning:
    source: PieceRefinedSourceSnapshot
    source_ref: str
    original: PieceSourceMeaning
    supplemental: PieceSupplementalMeaning


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
    return result


def refined_source_ref(source) -> str:
    return 'piece-refined:' + _sha(canonical_json_bytes(_source_payload(source)))


def _supplemental_meaning(answer, owner_id):
    """Adapt existing finite grammar, then bind every node to its answer source.

    The temporary text view is only a parser input. It is not retained as
    semantic source or saved original, nor joined to the actual original.
    The returned graph and all evidence use the answer owner's real envelope.
    """
    from piece_v2_generation import PieceSourceSnapshot
    from .source_kernel import _evidence_id
    frozen = freeze_supplemental_answer(answer)
    view = PieceSourceSnapshot(owner_id, answer.answer_id, answer.source_version,
                               answer.answer_text_private)
    parsed = build_piece_source_meaning(view, expected_owner_id=owner_id,
        expected_saved_input_id=answer.answer_id, expected_source_version=answer.source_version)
    _require(bool(frozen.evidence_refs))
    field = frozen.evidence_refs[0]
    evidence = []
    ids = {}
    for local in parsed.evidence:
        values = dict(source_span_id=local.source_span_id, field_path=field.field_path,
            element_index=field.element_index, field_utf8_start=field.field_utf8_start,
            field_utf8_end=field.field_utf8_end, scalar_start=local.scalar_start,
            scalar_end=local.scalar_end, utf8_start=field.field_utf8_start + local.utf8_start,
            utf8_end=field.field_utf8_start + local.utf8_end,
            field_sha256=field.field_sha256, literal_sha256=local.literal_sha256)
        eid = _evidence_id(envelope_id=frozen.envelope.envelope_id, **values)
        ids[local.evidence_id] = eid
        evidence.append(replace(local, evidence_id=eid,
            source_envelope_id=frozen.envelope.envelope_id, **values))
    graph = replace(parsed.graph,
        graph_id='piece-graph:' + _sha(canonical_json_bytes(
            [frozen.envelope.envelope_id, parsed.graph.graph_id])),
        source_envelope_id=frozen.envelope.envelope_id,
        nodes=tuple(replace(n, evidence_ids=tuple(ids[e] for e in n.evidence_ids))
                    for n in parsed.graph.nodes),
        edges=tuple(replace(e, evidence_ids=tuple(ids[r] for r in e.evidence_ids))
                    for e in parsed.graph.edges),
        owner_dispositions=tuple(replace(o, evidence_refs=tuple(ids[e] for e in o.evidence_refs))
                                 for o in parsed.graph.owner_dispositions))
    values = {f.name: getattr(parsed, f.name) for f in fields(PieceSourceMeaning)}
    values.update(envelope=frozen.envelope, graph=graph, evidence=tuple(evidence),
        sentences=tuple(replace(s, evidence_id=ids[s.evidence_id]) for s in parsed.sentences))
    return PieceSupplementalMeaning(**values, frozen_answer=frozen, grammar_owner_id=owner_id)


def validate_supplemental_meaning(meaning):
    _require(type(meaning) is PieceSupplementalMeaning
             and type(meaning.frozen_answer) is FrozenSupplementalAnswer)
    # Re-derive parser/evidence only, never the author. Saved re-read below
    # does not enter this function; this is generation-time source validation.
    _require(type(meaning.grammar_owner_id) is str and bool(meaning.grammar_owner_id.strip()))
    expected = _supplemental_meaning(meaning.frozen_answer.source, meaning.grammar_owner_id)
    # The grammar's local owner is not part of its graph/source identity.
    _require(meaning == expected, 'piece_refined_answer_evidence_binding')


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
    _require(source.supplemental_update_operation == 'ADD', 'piece_refined_update_not_supported')
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
    # This first slice adds a complete self-contained first-person account.
    # It cannot interpret a correction/withdrawal or resolve an answer's
    # "それ" from the question/original. Such updates stay unsupported.
    _require(not re.search(r'訂正|撤回|ではなく|じゃなく|違います|違った', answer.answer_text_private),
             'piece_refined_update_not_supported')
    original_meaning = build_piece_source_meaning(original,
        expected_owner_id=request.expected_owner_id,
        expected_saved_input_id=request.expected_saved_input_id,
        expected_source_version=request.expected_source_version)
    supplemental = _supplemental_meaning(answer, original.owner_id)
    _require(all(re.match(r'^(?:(?:以前|当時|今|現在|これから)[はも][、，,]\s*)?'
                         r'(?:私|わたし|僕|ぼく|俺|おれ)(?:は|が|にとって)', n.value)
                 or supplemental_feeling_time_span(supplemental, n) is not None
                 for n in supplemental.graph.nodes), 'piece_refined_answer_not_self_contained')
    return PieceRefinedMeaning(source, refined_source_ref(source), original_meaning, supplemental)


def _plans(meaning):
    from .piece_v1c import compile_piece_artifact_plan
    return PieceRefinedPlan(meaning.source_ref, compile_piece_artifact_plan(meaning.original),
                             compile_piece_artifact_plan(meaning.supplemental))


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
    _require(len(artifact.body_blocks) == count + len(plan.supplemental_plan.block_node_ids),
             'piece_refined_artifact_binding')
    for part, child_plan, blocks in (
            (meaning.original, plan.original_plan, artifact.body_blocks[:count]),
            (meaning.supplemental, plan.supplemental_plan, artifact.body_blocks[count:])):
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
        for part, child in ((meaning.original, plan.original_plan),
                            (meaning.supplemental, plan.supplemental_plan)))
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
