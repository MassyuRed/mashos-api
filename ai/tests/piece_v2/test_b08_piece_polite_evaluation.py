"""Source-bound finite evaluations across negative/past/modal polite forms.

Synthetic inputs. The source's register is not rewritten. A polite auxiliary
must not turn a past denial or qualified assessment into a present assertion.
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


TARGET = '自分の手で紙を折る時間'
TAIL = 'まだ、毎日続けるかは決めていません。'
BASES = ('大切', '大事', '重要', '必要', '好き', '苦手')
SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
# Expected meaning is specified independently of the production regex.
FORMS = (
    ('ではありません', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('ではありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('ではないです', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('ではなかったです', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('じゃありません', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('じゃないです', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃなかったです', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('かもしれません', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('とは限りません', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('だったかもしれません', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('だったとは限りません', 'AFFIRMATIVE', 'PAST', 'NON_UNIVERSAL'),
    ('ではないかもしれません', 'NEGATIVE', 'NONPAST', 'POSSIBLE'),
    ('ではないとは限りません', 'NEGATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('ではなかったかもしれません', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('ではなかったとは限りません', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
    ('じゃないかもしれません', 'NEGATIVE', 'NONPAST', 'POSSIBLE'),
    ('じゃないとは限りません', 'NEGATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('じゃなかったかもしれません', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('じゃなかったとは限りません', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
)


def outcome(text, **kwargs):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-polite-evaluation', 'v1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-polite-evaluation', source, source.owner_id,
        source.saved_input_id, source.source_version, **kwargs))
    return source, result


def assert_body_and_source(source, out, expected):
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    meaning = out.source_meaning
    assert meaning.envelope.raw_utf8 == source.original_text.encode('utf-8')
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert source.original_text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    for frame in meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert source.original_text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode('utf-8')
    frozen = asdict(meaning), asdict(out.artifact_plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(out.artifact_plan)) == frozen
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('base', BASES)
@pytest.mark.parametrize('ending,polarity,time,commitment', FORMS, ids=[f[0] for f in FORMS])
def test_finite_forms_keep_complete_predicate_and_inner_state(base, ending, polarity, time, commitment):
    viewpoint = '私は' if base in ('好き', '苦手') else '私にとって'
    text = viewpoint + TARGET + 'が' + base + ending + '。' + TAIL
    source, out = outcome(text)
    assert_body_and_source(source, out, viewpoint + '、' + TARGET + 'が' + base + ending + '。' + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert frame.construction == ('は' if base in ('好き', '苦手') else 'にとって')
    assert frame.kind == ('PERSONAL_PREFERENCE' if base in ('好き', '苦手') else 'PERSONAL_VALUE')
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert source.original_text[slice(*frame.scalar_parts[1])] == base + ending


@pytest.mark.parametrize('ending,polarity,time,commitment', FORMS, ids=[f[0] for f in FORMS])
def test_singleton_negation_past_and_modality_never_become_declarations(ending, polarity, time, commitment):
    text = '私にとって' + TARGET + 'が大切' + ending + '。'
    source, out = outcome(text)
    assert_body_and_source(source, out, '私にとって、' + TARGET + 'が大切' + ending + '。')
    assert out.artifact_plan.declaration_eligible is False
    assert 'declaration' not in out.artifact.eligible_formats
    _, requested = outcome(text, tier='premium', requested_format='declaration')
    assert requested.status == EngineStatus.UNAVAILABLE
    assert requested.artifact is None


@pytest.mark.parametrize('speaker', SPEAKERS)
def test_reference_and_public_role_transform_consume_the_same_new_evaluation(speaker):
    target = '友人のｼﾞｮｰｼﾞさんと落ち着いて話す時間'
    text = (speaker + 'にとって' + target + 'が大切ではありませんでした。'
            + speaker + 'はその時間が苦手とは限りません。' + TAIL)
    source, out = outcome(text)
    expected = (speaker + 'にとって、友人と落ち着いて話す時間が大切ではありませんでした。'
                'その時間が苦手とは限りません。' + TAIL)
    assert_body_and_source(source, out, expected)
    first, second = out.source_meaning.personal_evaluations
    assert (first.polarity, first.temporal_scope, first.commitment) == ('NEGATIVE', 'PAST', 'ASSERTED')
    assert (second.polarity, second.temporal_scope, second.commitment) == ('AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL')
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == first.node_id
    assert ref.reference_node_id == second.node_id
    assert source.original_text[slice(*ref.antecedent_scalar_span)] == target
    assert source.original_text[slice(*ref.reference_scalar_span)] == 'その時間'
    assert 'ｼﾞｮｰｼﾞさん' not in expected


@pytest.mark.parametrize('marker,relation', (
    ('ので', 'SOURCE_EXPLICIT_REASON'), ('なら', 'SOURCE_EXPLICIT_CONDITION'),
    ('ならば', 'SOURCE_EXPLICIT_CONDITION'), ('けれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('けれども', 'SOURCE_EXPLICIT_CONCESSION'),
))
@pytest.mark.parametrize('predicate,polarity,time,commitment', (
    ('必要かもしれません', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('大切ではありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('必要ではなかったとは限りません', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
))
def test_written_scope_stays_attached_to_the_complete_polite_evaluation(marker, relation, predicate, polarity, time, commitment):
    premise = '予定が重なる' + marker
    text = premise + '、僕にとって' + TARGET + 'が' + predicate + '。' + TAIL
    source, out = outcome(text)
    assert_body_and_source(source, out, premise + '、僕にとって、' + TARGET + 'が' + predicate + '。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == relation
    assert source.original_text[slice(*scope.scope_scalar_span)] == premise
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert scope.node_id == frame.node_id
    assert out.artifact_plan.declaration_eligible is False


@pytest.mark.parametrize('degree', ('とても', 'かなり', '少し', 'あまり'))
@pytest.mark.parametrize('predicate', ('好きではないです', '苦手じゃありませんでした', '必要だったかもしれません'))
def test_degree_is_part_of_the_source_predicate_not_a_certainty_change(degree, predicate):
    viewpoint = 'わたしにとって' if predicate.startswith('必要') else 'わたしは'
    text = viewpoint + TARGET + 'が' + degree + predicate + '。' + TAIL
    source, out = outcome(text)
    assert_body_and_source(source, out, viewpoint + '、' + TARGET + 'が' + degree + predicate + '。' + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert source.original_text[slice(*frame.scalar_parts[1])] == degree + predicate


UNSUPPORTED = (
    '私にとって' + TARGET + 'が必要ではありませんかもしれません。',
    '私にとって' + TARGET + 'が必要でしたかもしれません。',
    '私にとって' + TARGET + 'が必要ではないですとは限りません。',
    '私にとって' + TARGET + 'が必要かもしれませんでした。',
    '私にとって' + TARGET + 'が必要とは限りませんでした。',
    '私にとって' + TARGET + 'が必要ではありませんとは言っていません。',
    '私は' + TARGET + 'が好きかもしれませんと友人が話した。',
    '友人にとって' + TARGET + 'が必要かもしれません。',
    '私にとってその時間が必要かもしれません。',
    '私にとって' + TARGET + 'は必要かもしれません。',
    '私は' + TARGET + 'が必要かもしれません。',
    '私にとって大切ではありませんのは' + TARGET + 'です。',
    '私が好きかもしれませんのは' + TARGET + 'です。',
)


@pytest.mark.parametrize('text', UNSUPPORTED)
def test_outer_negation_reports_unbound_references_and_invalid_stacking_are_not_admitted(text):
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('field,value', (
    ('polarity', 'AFFIRMATIVE'), ('temporal_scope', 'NONPAST'), ('commitment', 'ASSERTED'),
))
def test_altered_frame_cannot_authorize_a_different_reading(field, value):
    text = '私にとって' + TARGET + 'が必要ではなかったかもしれません。' + TAIL
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    frame, = out.source_meaning.personal_evaluations
    forged = replace(out.source_meaning, personal_evaluations=(replace(frame, **{field: value}),))
    with pytest.raises(ValueError):
        realize_piece_artifact(forged, out.artifact_plan, tier='free', requested_format=None)
