"""Horizontal gaps after a written self topic do not change its direct object.

Synthetic, code-disabled Piece-component regression. This exercises the real
source/plan/writer, not common-Engine, HTTP, saved-record or native integration.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_source import _direct_transitive_expression
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, generate_piece_artifact, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot

TAIL = 'まだ、毎日続けるかは決めていません。'


def run(text, *, requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-topic-gap', 'v1', text)
    request = PieceGenerationRequest('synthetic-topic-gap', source, source.owner_id,
        source.saved_input_id, source.source_version, tier='premium',
        requested_format=requested_format)
    return generate_piece_artifact(request)


def checked(text):
    out = run(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert meaning.envelope.raw_sha256 == hashlib.sha256(text.encode('utf-8')).hexdigest()
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode('utf-8')[ev.utf8_start:ev.utf8_end] == node.value.encode('utf-8')
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    assert realize_piece_artifact(meaning, plan, tier='premium', requested_format=None) == artifact
    assert run(text).artifact == artifact
    candidate = artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(artifact.piece_text.encode('utf-8')).hexdigest()
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not candidate['production_enabled'] and not out.automatic_progression
    return out


@pytest.mark.parametrize('target', ('読書', 'メモ', '家族'))
@pytest.mark.parametrize('predicate', (
    '望んでいる', '望んでいない', '望んでいた',
    '望んでいなかったかもしれない', '望んでいませんでした',
))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
def test_simple_nominal_target_and_full_predicate_survive_topic_gap(target, predicate, gap):
    plain = '私は、' + target + 'を' + predicate + '。'
    raw = '私は、' + gap + target + 'を' + predicate + '。'
    parsed = _direct_transitive_expression(raw)
    assert parsed is not None
    assert parsed['object'] == target and parsed['predicate'] == predicate
    assert parsed.span('object') == (len('私は、' + gap), len('私は、' + gap + target))
    actual = checked(raw + TAIL)
    assert actual.artifact == checked(plain + TAIL).artifact
    assert actual.artifact.piece_text == plain + TAIL


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('comma', ('、', '，', ','))
def test_written_speaker_and_mixed_horizontal_gaps_are_not_part_of_object(speaker, comma):
    raw = speaker + 'は' + comma + ' \t\u3000' + '読書を望んでいなかったかもしれない。'
    actual = checked(raw + TAIL)
    assert actual.artifact.piece_text == speaker + 'は、読書を望んでいなかったかもしれない。' + TAIL


@pytest.mark.parametrize('scope', (
    '気持ちが落ち着かなかったので', '予定が合うなら',
    '予定が合うならば', 'まだ迷っていたけれど', 'まだ迷っていたけれども',
    '当時は',
))
def test_scope_remains_outside_the_object_and_does_not_become_a_pledge(scope):
    plain = scope + '、私は、読書を望んでいなかったかもしれない。'
    raw = scope + '、\u3000私は、\u3000読書を望んでいなかったかもしれない。'
    actual = checked(raw + TAIL)
    assert actual.artifact == checked(plain + TAIL).artifact
    bound, = actual.source_meaning.expression_scopes
    assert raw[slice(*bound.scope_scalar_span)] == scope
    assert raw[slice(*bound.expression_scalar_span)] == '私は、\u3000読書を望んでいなかったかもしれない。'
    assert not actual.artifact_plan.declaration_eligible
    for fmt in ('quote', 'declaration'):
        assert run(raw + TAIL, requested_format=fmt).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('gap', (' ', '\t', '\u3000', ' \t\u3000'))
def test_reference_binds_the_target_not_its_leading_gap(gap):
    target = '一人で静かに手帳を開く時間'
    first = '僕は、' + gap + target + 'を大切にしていた。'
    following = '僕は、' + gap + 'その時間を望んでいなかったかもしれない。'
    raw = '🌱を見た。\r\n' + first + following + TAIL
    plain = '🌱を見た。\r\n僕は、' + target + 'を大切にしていた。僕は、その時間を望んでいなかったかもしれない。' + TAIL
    actual = checked(raw)
    assert actual.artifact == checked(plain).artifact
    ref, = actual.source_meaning.nominal_references
    assert raw[slice(*ref.antecedent_scalar_span)] == target
    assert raw[slice(*ref.reference_scalar_span)] == 'その時間'
    assert ref.antecedent_scalar_span[0] == raw.index(target)
    assert ref.reference_scalar_span[0] == raw.index('その時間')


@pytest.mark.parametrize('gap', ('\n', '\r', '\r\n', '\v', '\f', '\u00a0', '\u2028', '\u200b', '、\u3000'))
def test_other_separators_do_not_gain_a_direct_object(gap):
    raw = '私は、' + gap + '読書を望んでいなかったかもしれない。'
    assert _direct_transitive_expression(raw) is None
    assert run(raw + TAIL).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('raw', (
    '読書を望んでいなかった。',
    '友人は、\u3000読書を望んでいなかった。',
    '私は、\u3000その時間を望んでいなかった。',
    '私は、\u3000読書を望んでいましたと聞いた。',
    '私は、\u3000読書を望んでいなかったかもしれないとは限らない。',
))
def test_gap_does_not_supply_subject_reference_or_unwritten_certainty(raw):
    assert run(raw + TAIL).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('reference', 'evidence', 'scope', 'plan'))
def test_forged_source_coordinates_and_plan_remain_rejected(mutation):
    raw = ('僕は、\u3000静かに考える時間を大切にしていた。'
           'まだ迷っていたけれど、僕は、\u3000その時間を望んでいなかったかもしれない。' + TAIL)
    out = checked(raw)
    meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'reference':
        ref, = meaning.nominal_references
        meaning = replace(meaning, nominal_references=(replace(ref,
            reference_scalar_span=(ref.reference_scalar_span[0] - 1, ref.reference_scalar_span[1])),))
    elif mutation == 'evidence':
        ev = meaning.evidence[0]
        meaning = replace(meaning, evidence=(replace(ev, utf8_start=ev.utf8_start + 1), *meaning.evidence[1:]))
    elif mutation == 'scope':
        meaning = replace(meaning, expression_scopes=())
    else:
        plan = replace(plan, block_node_ids=(plan.block_node_ids[0][:-1],))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='premium', requested_format=None)
