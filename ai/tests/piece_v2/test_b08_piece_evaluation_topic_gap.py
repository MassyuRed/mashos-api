"""A horizontal topic gap is not part of a finite evaluation's target.

Uses real Piece source/plan/author/validation components, not a simulated
Engine. Saved-preview, HTTP and native-renderer acceptance are separate.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_source import _EVALUATIVE_FINITE
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, generate_piece_artifact, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot

TAIL = 'まだ、毎日続けるかは決めていません。'
EVALUATIONS = (
    ('は', '好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('は', '苦手ではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('は', '好きではなかったかもしれません', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('は', '苦手とは限らない', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('にとって', '大切でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('にとって', '必要ではありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('にとって', '重要だったとは限りません', 'AFFIRMATIVE', 'PAST', 'NON_UNIVERSAL'),
    ('にとって', '少し大事かもしれない', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
)


def run(text, *, requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-evaluation-gap', 'v1', text)
    return generate_piece_artifact(PieceGenerationRequest(
        'synthetic-evaluation-gap', source, source.owner_id, source.saved_input_id,
        source.source_version, tier='premium', requested_format=requested_format))


def checked(text):
    out = run(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    raw = text.encode('utf-8')
    assert meaning.envelope.raw_utf8 == raw
    assert meaning.envelope.raw_sha256 == hashlib.sha256(raw).hexdigest()
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert raw[evidence.utf8_start:evidence.utf8_end] == node.value.encode('utf-8')
    for frame in meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    assert realize_piece_artifact(meaning, plan, tier='premium', requested_format=None) == artifact
    assert run(text).artifact == artifact
    candidate = artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(artifact.piece_text.encode('utf-8')).hexdigest()
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not candidate['production_enabled'] and not out.automatic_progression
    return out


@pytest.mark.parametrize('construction,predicate,polarity,temporal,commitment', EVALUATIONS)
@pytest.mark.parametrize('target', ('読書', 'メモ', '家族'))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
def test_finite_evaluation_keeps_target_predicate_and_commitment(
        construction, predicate, polarity, temporal, commitment, target, gap):
    topic = '私' + construction + '、'
    plain = topic + target + 'が' + predicate + '。'
    sentence = topic + gap + target + 'が' + predicate + '。'
    parsed = _EVALUATIVE_FINITE.fullmatch(sentence)
    assert parsed is not None
    assert parsed['target'] == target and parsed['predicate'] == predicate
    assert parsed.span('target') == (len(topic + gap), len(topic + gap + target))
    out = checked(sentence + TAIL)
    assert out.artifact == checked(plain + TAIL).artifact
    assert out.artifact.piece_text == plain + TAIL
    frame, = out.source_meaning.personal_evaluations
    assert sentence[slice(*frame.scalar_parts[0])] == '私'
    assert sentence[slice(*frame.scalar_parts[1])] == predicate
    assert sentence[slice(*frame.scalar_parts[2])] == target
    assert (frame.construction, frame.polarity, frame.temporal_scope, frame.commitment) == (
        construction, polarity, temporal, commitment)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('construction,predicate', (('は', '好きです'), ('にとって', '必要でした')))
def test_written_viewpoint_and_mixed_horizontal_gap(speaker, construction, predicate):
    topic = speaker + construction
    plain = topic + '、読書が' + predicate + '。' + TAIL
    raw = topic + '， \t\u3000読書が' + predicate + '。' + TAIL
    out = checked(raw)
    assert out.artifact == checked(plain).artifact
    frame, = out.source_meaning.personal_evaluations
    assert raw[slice(*frame.scalar_parts[0])] == speaker
    assert frame.construction == construction


@pytest.mark.parametrize('comma', ('', '、', '，', ','))
def test_existing_optional_comma_is_not_required_by_gap(comma):
    raw = '私は' + comma + '\u3000読書が好きです。' + TAIL
    assert checked(raw).artifact == checked('私は読書が好きです。' + TAIL).artifact


@pytest.mark.parametrize('scope', ('予定が合うなら', '気持ちが落ち着かなかったので',
                                   'まだ迷っていたけれど', '当時は'))
@pytest.mark.parametrize('construction,predicate', (
    ('は', '好きではなかったかもしれません'),
    ('にとって', '必要だったとは限りません'),
))
def test_outer_scope_remains_outside_evaluation_and_cannot_be_a_pledge(scope, construction, predicate):
    expression = '私' + construction + '、\u3000読書が' + predicate + '。'
    raw = scope + '、\u3000' + expression + TAIL
    plain = scope + '、私' + construction + '、読書が' + predicate + '。' + TAIL
    out = checked(raw)
    assert out.artifact == checked(plain).artifact
    bound, = out.source_meaning.expression_scopes
    frame, = out.source_meaning.personal_evaluations
    assert raw[slice(*bound.scope_scalar_span)] == scope
    assert raw[slice(*bound.expression_scalar_span)] == expression
    assert raw[slice(*frame.scalar_parts[2])] == '読書'
    assert not out.artifact_plan.declaration_eligible
    assert run(raw, requested_format='declaration').status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('gap', (' ', '\t', '\u3000', ' \t\u3000'))
@pytest.mark.parametrize('reference_gap', ('', '\u3000'))
def test_reference_coordinates_do_not_include_either_topic_gap(gap, reference_gap):
    target = '一人で静かに手帳を開く時間'
    prefix = '🌱を見た。\r\n'
    plain = (prefix + '僕にとって、' + target + 'が大切でした。'
             '僕は、その時間が好きではなかったかもしれません。' + TAIL)
    raw = (prefix + '僕にとって、' + gap + target + 'が大切でした。'
           '僕は、' + reference_gap + 'その時間が好きではなかったかもしれません。' + TAIL)
    out = checked(raw)
    assert out.artifact == checked(plain).artifact
    ref, = out.source_meaning.nominal_references
    assert raw[slice(*ref.antecedent_scalar_span)] == target
    assert raw[slice(*ref.reference_scalar_span)] == 'その時間'
    assert ref.antecedent_scalar_span[0] == raw.index(target)
    assert ref.reference_scalar_span[0] == raw.index('その時間')
    frames = out.source_meaning.personal_evaluations
    assert raw[slice(*frames[0].scalar_parts[2])] == target
    assert raw[slice(*frames[1].scalar_parts[2])] == 'その時間'


@pytest.mark.parametrize('gap', ('\n', '\r', '\r\n', '\v', '\f', '\u00a0', '\u2028', '\u200b', '、\u3000'))
def test_other_separators_do_not_admit_simple_noun_evaluation(gap):
    assert run('私は、' + gap + '読書が好きではなかったかもしれません。' + TAIL).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('raw', (
    '読書が好きです。',
    '友人は、\u3000読書が好きです。',
    '私は、\u3000その時間が好きです。',
    '私は、\u3000読書が好きですと聞いた。',
    '私は、\u3000読書が好きかもしれないとは限らない。',
    '私は、\u3000読書が必要です。',
    '私が、\u3000読書が好きです。',
))
def test_gap_does_not_infer_a_viewpoint_referent_or_new_predicate(raw):
    assert run(raw + TAIL).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('frame', 'evidence', 'scope', 'plan'))
def test_forged_source_bindings_still_fail_before_realization(mutation):
    raw = '予定が合うなら、私は、\u3000読書が好きではなかったかもしれません。' + TAIL
    out = checked(raw)
    meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'frame':
        frame, = meaning.personal_evaluations
        a, b = frame.scalar_parts[2]
        meaning = replace(meaning, personal_evaluations=(replace(frame,
            scalar_parts=(*frame.scalar_parts[:2], (a - 1, b))),))
    elif mutation == 'evidence':
        first = meaning.evidence[0]
        meaning = replace(meaning, evidence=(replace(first, utf8_start=first.utf8_start + 1),
                                             *meaning.evidence[1:]))
    elif mutation == 'scope':
        meaning = replace(meaning, expression_scopes=())
    else:
        plan = replace(plan, block_node_ids=(plan.block_node_ids[0][:-1],))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='premium', requested_format=None)
