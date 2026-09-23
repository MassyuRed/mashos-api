"""Source-written time topics qualify evaluations, not the referenced object.

Synthetic inputs only. Relative time is never resolved using a clock, nor is a
past/current contrast turned into a cause, progress claim, or future promise.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


TARGET = '窓辺で草花を眺めて過ごす時間'
TAIL = 'まだ、毎日予定を空けられるとは限りません。'
SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')


def outcome(text, **kwargs):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-time-scope', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-time-scope', source, source.owner_id,
        source.saved_input_id, source.source_version, **kwargs))
    return source, out


def assert_artifact(source, out, expected):
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == source.original_text.encode('utf-8')
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert source.original_text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    for scope in meaning.expression_scopes:
        assert scope.relation == 'SOURCE_EXPLICIT_TIME_CONTEXT'
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert source.original_text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode('utf-8')
    for frame in meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert source.original_text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode('utf-8')
    ordered = tuple(node for block in plan.block_node_ids for node in block)
    assert ordered == tuple(node.node_id for node in meaning.graph.nodes)
    assert plan.declaration_eligible is False
    assert out.artifact.eligible_formats == ('short_essay',)
    frozen = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == frozen
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_past_and_current_evaluations_keep_separate_time_topics_and_one_referent(speaker, order):
    past = speaker + 'は' + TARGET + 'が苦手でした。'
    if order == 'focus':
        past = speaker + 'が苦手だったのは' + TARGET + 'です。'
    text = '以前は、' + past + '今は、' + speaker + 'はその時間が好きかもしれません。' + TAIL
    expected = ('以前は、' + speaker + 'は' + TARGET
                + ('が苦手だった。' if order == 'focus' else 'が苦手でした。')
                + '今は、' + speaker + 'はその時間が好きかもしれません。' + TAIL)
    source, out = outcome(text)
    assert_artifact(source, out, expected)
    first, second = out.source_meaning.personal_evaluations
    assert (first.polarity, first.temporal_scope, first.commitment) == ('AFFIRMATIVE', 'PAST', 'ASSERTED')
    assert (second.polarity, second.temporal_scope, second.commitment) == ('AFFIRMATIVE', 'NONPAST', 'POSSIBLE')
    a, b = out.source_meaning.expression_scopes
    assert source.original_text[slice(*a.scope_scalar_span)] == '以前は'
    assert source.original_text[slice(*b.scope_scalar_span)] == '今は'
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == first.node_id and ref.reference_node_id == second.node_id
    assert source.original_text[slice(*ref.antecedent_scalar_span)] == TARGET
    assert source.original_text[slice(*ref.reference_scalar_span)] == 'その時間'
    assert first.scalar_parts[2] == ref.antecedent_scalar_span


@pytest.mark.parametrize('time_topic', ('以前は', '以前も', '当時は', '当時も', '今は', '今も', '現在は', '現在も'))
@pytest.mark.parametrize('viewpoint,predicate,state', (
    ('私にとって', '大切ではありませんでした', ('NEGATIVE', 'PAST', 'ASSERTED')),
    ('私は', '苦手とは限りません', ('AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL')),
))
def test_written_time_does_not_overwrite_predicate_tense_polarity_or_commitment(time_topic, viewpoint, predicate, state):
    text = time_topic + '、' + viewpoint + TARGET + 'が' + predicate + '。' + TAIL
    source, out = outcome(text)
    assert_artifact(source, out, text)
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == state
    assert source.original_text[slice(*frame.scalar_parts[1])] == predicate
    scope, = out.source_meaning.expression_scopes
    assert scope.marker == time_topic[-1]
    assert source.original_text[slice(*scope.scope_scalar_span)] == time_topic
    assert out.source_meaning.graph.nodes[0].node_kind == 'PIECE_SOURCE_TIME_SCOPED_EXPRESSION'


def test_public_role_chain_and_past_negative_remain_inside_their_time_context():
    text = ('当時は、私にとって友人のｼﾞｮｰｼﾞさんの同僚のメアリー・アンさんと話す時間が大切ではありませんでした。'
            '今は、私はその時間が苦手とは限りません。' + TAIL)
    expected = ('当時は、私にとって友人の同僚と話す時間が大切ではありませんでした。'
                '今は、私はその時間が苦手とは限りません。' + TAIL)
    source, out = outcome(text)
    assert_artifact(source, out, expected)
    first, second = out.source_meaning.personal_evaluations
    assert (first.polarity, first.temporal_scope) == ('NEGATIVE', 'PAST')
    assert second.commitment == 'NON_UNIVERSAL'
    assert 'ｼﾞｮｰｼﾞ' not in expected and 'メアリー' not in expected


def test_time_scope_never_invents_an_unwritten_change_or_explanation():
    text = '今は、私にとって' + TARGET + 'が大切です。' + TAIL
    source, out = outcome(text)
    assert_artifact(source, out, text)
    assert len(out.source_meaning.expression_scopes) == 1
    assert not any(edge.relation in ('CHANGE', 'CAUSE', 'IMPROVEMENT') for edge in out.source_meaning.graph.edges)


@pytest.mark.parametrize('separator', ('、', '，', ',', '、\t', '、　'))
def test_time_scope_has_exact_source_coordinates_across_written_separators(separator):
    text = '\n\t以前は' + separator + '僕は' + TARGET + 'が苦手でした。\r\n今は、僕はその時間が好きです。' + TAIL
    expected = '以前は、僕は' + TARGET + 'が苦手でした。今は、僕はその時間が好きです。' + TAIL
    source, out = outcome(text)
    assert_artifact(source, out, expected)


@pytest.mark.parametrize('body', (
    '私にとって' + TARGET + 'が大切です。',
    '私が好きなのは' + TARGET + 'です。',
))
def test_one_time_qualified_evaluation_is_not_an_unqualified_quote_or_declaration(body):
    text = '今は、' + body
    source, out = outcome(text)
    expected = '今は、' + (body if body.startswith('私にとって') else '私は' + TARGET + 'が好きです。')
    assert_artifact(source, out, expected)
    for fmt in ('quote', 'declaration'):
        _, requested = outcome(text, tier='premium', requested_format=fmt)
        assert requested.status == EngineStatus.UNAVAILABLE and requested.artifact is None


UNSUPPORTED = (
    '今は、友人にとって' + TARGET + 'が必要です。',
    '今は、' + TARGET + 'が大切です。',
    '今は私は' + TARGET + 'が好きです。',
    '今後は、私にとって' + TARGET + 'が大切です。',
    '今は、僕はその時間が好きです。',
    '以前は、僕は' + TARGET + 'が好きだと友人が話しました。',
    '今は、私にとって' + TARGET + 'が必要ではありませんとは言っていません。',
    '以前は、今は、僕は' + TARGET + 'が好きです。',
)


@pytest.mark.parametrize('text', UNSUPPORTED)
def test_time_topic_does_not_license_missing_speakers_references_or_nested_reports(text):
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


def test_two_possible_antecedents_are_not_resolved_by_selecting_the_latest_time():
    text = ('以前は、私にとって窓辺で草花を眺める時間が大切でした。'
            '今は、私にとって自分の手で紙を折る時間が必要です。'
            '今は、私はその時間が好きです。' + TAIL)
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('change', ('relation', 'marker', 'span', 'removed'))
def test_altered_time_scope_cannot_authorize_dropping_or_changing_the_qualifier(change):
    text = '当時は、私にとって' + TARGET + 'が必要ではありませんでした。' + TAIL
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    scope, = out.source_meaning.expression_scopes
    if change == 'relation':
        altered = (replace(scope, relation='SOURCE_EXPLICIT_REASON'),)
    elif change == 'marker':
        altered = (replace(scope, marker='も'),)
    elif change == 'span':
        altered = (replace(scope, scope_scalar_span=(1, scope.scope_scalar_span[1])),)
    else:
        altered = ()
    forged = replace(out.source_meaning, expression_scopes=altered)
    with pytest.raises(ValueError):
        realize_piece_artifact(forged, out.artifact_plan, tier='free', requested_format=None)
