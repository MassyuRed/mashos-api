"""Private Piece evidence from one explicitly selected record answer."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime
import hashlib
import re
from typing import TYPE_CHECKING
from uuid import UUID

from piece_v2_content_policy import unavailable
from piece_v2_contract import canonical_json_bytes
from .cores.analysis.source_adapter import DEEP_INSIGHT_ANSWER_ROLE
from .piece_source import PieceSourceMeaning, build_piece_source_meaning
from .source_kernel import _evidence_id, _source_envelope_id

if TYPE_CHECKING:
    from piece_v2_generation import PieceSourceSnapshot


SOURCE_VERSION = 'piece.deep_insight_answer.v1'
SOURCE_KIND = 'deep_insight_record_answer'
ANSWER_FIELD = 'answer_text_private'


@dataclass(frozen=True, slots=True, repr=False)
class PieceDeepInsightSourceSnapshot:
    """From the owner-bound saved source adapter; no question prose is evidence."""

    original: PieceSourceSnapshot
    question_id: str
    answer_text: str
    answered_at: str
    source_commitment: str


@dataclass(frozen=True, slots=True, repr=False)
class PieceDeepInsightAnswerMeaning(PieceSourceMeaning):
    selected_source: PieceDeepInsightSourceSnapshot | None = None


def deep_insight_source_ref(source: PieceDeepInsightSourceSnapshot) -> str:
    from piece_v2_generation import PieceSourceSnapshot

    try:
        if (type(source) is not PieceDeepInsightSourceSnapshot
                or type(source.original) is not PieceSourceSnapshot
                or type(source.original.saved_original_json) is not bytes
                or source.question_id != str(UUID(source.question_id))
                or source.question_id == source.original.saved_input_id
                or type(source.answer_text) is not str or not source.answer_text.strip()
                or datetime.fromisoformat(source.answered_at).utcoffset() is None
                or type(source.source_commitment) is not str
                or not re.fullmatch(r'sha256:[0-9a-f]{64}', source.source_commitment)):
            raise ValueError
        payload = [SOURCE_VERSION, source.original.owner_id, source.original.saved_input_id,
            source.original.source_version, hashlib.sha256(source.original.saved_original_json).hexdigest(),
            source.question_id, source.answered_at, source.source_commitment,
            hashlib.sha256(source.answer_text.encode()).hexdigest()]
        return 'piece-deep-insight:' + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    except (ValueError, TypeError, AttributeError):
        raise unavailable('piece_deep_insight_source_binding') from None


def build_deep_insight_answer_meaning(source: PieceDeepInsightSourceSnapshot) -> PieceDeepInsightAnswerMeaning:
    from piece_v2_generation import PieceSourceSnapshot

    source_ref = deep_insight_source_ref(source)
    # The established grammar supplies syntax. All persisted provenance and
    # evidence below use the selected answer's own ID and role.
    parsed = build_piece_source_meaning(
        PieceSourceSnapshot(source.original.owner_id, source.question_id, SOURCE_VERSION, source.answer_text),
        expected_owner_id=source.original.owner_id, expected_saved_input_id=source.question_id,
        expected_source_version=SOURCE_VERSION)
    encoding = 'CMEE_PIECE_DEEP_INSIGHT_ANSWER_FRAME_UTF8_V1'
    prefix = f'{encoding}\n{source_ref}\n'.encode()
    raw = prefix + parsed.envelope.raw_utf8
    envelope = replace(parsed.envelope, source_role=DEEP_INSIGHT_ANSWER_ROLE,
        source_schema_version=SOURCE_VERSION, source_encoding=encoding,
        raw_utf8=raw, raw_sha256=hashlib.sha256(raw).hexdigest())
    envelope = replace(envelope, envelope_id=_source_envelope_id(
        source_record_id=envelope.source_record_id, source_role=envelope.source_role,
        source_schema_version=envelope.source_schema_version, source_contract_version=envelope.source_contract_version,
        source_encoding=envelope.source_encoding, label_contract_id=envelope.label_contract_id,
        label_contract_digest=envelope.label_contract_digest, raw_sha256=envelope.raw_sha256))
    ids, evidence = {}, []
    for ref in parsed.evidence:
        identity = asdict(ref)
        del identity['evidence_id'], identity['source_envelope_id']
        identity['field_path'] = ANSWER_FIELD
        for name in ('field_utf8_start', 'field_utf8_end', 'utf8_start', 'utf8_end'):
            identity[name] += len(prefix)
        evidence_id = _evidence_id(envelope_id=envelope.envelope_id, **identity)
        ids[ref.evidence_id] = evidence_id
        evidence.append(replace(ref, evidence_id=evidence_id,
            source_envelope_id=envelope.envelope_id, **identity))
    graph = replace(parsed.graph,
        graph_id='piece-graph:' + hashlib.sha256(canonical_json_bytes(
            [envelope.envelope_id, parsed.graph.graph_id])).hexdigest(),
        source_envelope_id=envelope.envelope_id,
        nodes=tuple(replace(node, evidence_ids=tuple(ids[ref] for ref in node.evidence_ids))
                    for node in parsed.graph.nodes),
        edges=tuple(replace(edge, evidence_ids=tuple(ids[ref] for ref in edge.evidence_ids))
                    for edge in parsed.graph.edges),
        owner_dispositions=tuple(replace(owner, evidence_refs=tuple(ids[ref] for ref in owner.evidence_refs))
                                 for owner in parsed.graph.owner_dispositions))
    values = {item.name: getattr(parsed, item.name) for item in fields(PieceSourceMeaning)}
    values.update(envelope=envelope, graph=graph, evidence=tuple(evidence),
        sentences=tuple(replace(sentence, evidence_id=ids[sentence.evidence_id])
                        for sentence in parsed.sentences))
    return PieceDeepInsightAnswerMeaning(**values, selected_source=source)


def build_deep_insight_piece_meaning(request):
    from .piece_refined import PieceRefinedMeaning

    source = request.source
    source_ref = deep_insight_source_ref(source)
    original = build_piece_source_meaning(source.original,
        expected_owner_id=request.expected_owner_id,
        expected_saved_input_id=request.expected_saved_input_id,
        expected_source_version=request.expected_source_version)
    return PieceRefinedMeaning(source, source_ref, original, build_deep_insight_answer_meaning(source))


def validate_deep_insight_piece_source(source: PieceDeepInsightSourceSnapshot):
    """Check both user-authored partitions before exposing this selection."""
    from .piece_refined import _plans
    from .piece_v1c import PieceGenerationRequest
    from .preparation_sources import piece_model_material, piece_model_field_slots

    deep_insight_source_ref(source)
    original = source.original
    meaning = build_deep_insight_piece_meaning(PieceGenerationRequest('piece-deep-insight-source-admission',
        source, original.owner_id, original.saved_input_id, original.source_version))
    plan = _plans(meaning)
    try:
        slots = piece_model_field_slots(piece_model_material(source, expected_owner_id=original.owner_id))
    except ValueError:
        raise unavailable('piece_model_block_partition') from None
    if len(slots) != len(plan.original_plan.block_node_ids) + len(plan.supplemental_plan.block_node_ids):
        raise unavailable('piece_model_block_partition')
