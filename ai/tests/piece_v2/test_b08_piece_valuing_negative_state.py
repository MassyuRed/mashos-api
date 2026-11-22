"""Preserve an explicit negative valuing state, not a negative wish.

Real disabled Piece source/plan/writer checks; no common-engine, HTTP,
saved-preview, database or device acceptance is implied.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_source import _direct_transitive_expression
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, generate_piece_artifact, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, _FOCUS, _transitive_predicate_forms

TARGET = '予定を詰めずに一人で静かに考える時間'
TAIL = '今の過ごし方を振り返っています。'
FORMS = (
    '大切にしていない', '大切にしていません',
    '大切にしていなかった', '大切にしていませんでした',
    '大切にしていないかもしれない', '大切にしていないかもしれません',
    '大切にしていないとは限らない', '大切にしていないとは限りません',
    '大切にしていなかったかもしれない', '大切にしていなかったかもしれません',
    '大切にしていなかったとは限らない', '大切にしていなかったとは限りません',
)
FOCAL_FORMS = tuple(p for p in FORMS if 'ません' not in p and '限りません' not in p)


def run(text, *, requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-valuing-state', 'v1', text)
    return generate_piece_artifact(PieceGenerationRequest(
        'synthetic-valuing-state', source, source.owner_id, source.saved_input_id,
        source.source_version, tier='premium', requested_format=requested_format))


def checked(text):
    out = run(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    raw = text.encode('utf-8')
    assert meaning.envelope.raw_utf8 == raw
    assert meaning.envelope.raw_sha256 == hashlib.sha256(raw).hexdigest()
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert raw[ev.utf8_start:ev.utf8_end] == node.value.encode('utf-8')
    assert realize_piece_artifact(meaning, plan, tier='premium', requested_format=None) == artifact
    assert run(text).artifact == artifact
    candidate = artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(artifact.piece_text.encode('utf-8')).hexdigest()
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not candidate['production_enabled'] and not out.automatic_progression
    return out


@pytest.mark.parametrize('predicate', FORMS)
@pytest.mark.parametrize('target', (TARGET, '読書'))
def test_direct_state_keeps_negation_register_time_and_modal(predicate, target):
    sentence = '私は、\u3000' + target + 'を' + predicate + '。'
    parsed = _direct_transitive_expression(sentence)
    assert parsed is not None
    assert parsed['predicate'] == predicate and parsed['object'] == target
    assert sentence[slice(*parsed.span('predicate'))] == predicate
    out = checked(sentence + TAIL)
    assert out.artifact.piece_text == '私は、' + target + 'を' + predicate + '。' + TAIL
    assert out.artifact_plan.duties[0].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'
    assert 'したくない' not in out.artifact.piece_text
    assert not out.artifact_plan.declaration_eligible
    assert run(sentence + TAIL, requested_format='declaration').status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('predicate', FOCAL_FORMS)
@pytest.mark.parametrize('speaker', ('私', '僕'))
def test_focal_state_keeps_same_predicate_and_written_author(predicate, speaker):
    sentence = speaker + 'が' + predicate + 'のは、' + TARGET + 'です。'
    parsed = _FOCUS.fullmatch(sentence)
    assert parsed is not None
    assert parsed['predicate'] == predicate and parsed['object'] == TARGET
    out = checked(sentence)
    assert out.artifact.piece_text == speaker + 'は、' + TARGET + 'を' + predicate + '。'
    assert out.artifact_plan.duties[0].operation == 'SOURCE_FOCAL_TO_FIRST_PERSON'
    if 'なかった' in predicate or 'かもしれ' in predicate or 'とは限' in predicate:
        assert not out.artifact_plan.declaration_eligible
        assert run(sentence, requested_format='declaration').status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_polite_state_keeps_each_explicit_self_spelling(speaker):
    raw = speaker + 'は、' + TARGET + 'を大切にしていませんでした。'
    assert checked(raw).artifact.piece_text == raw


@pytest.mark.parametrize('scope', ('予定が合うなら', '予定が合うならば', '忙しかったので',
                                   'まだ迷っていたけれど', 'まだ迷っていたけれども', '当時は'))
@pytest.mark.parametrize('focal', (False, True))
def test_outer_scope_is_not_completed_or_changed_into_an_intention(scope, focal):
    predicate = '大切にしていなかったかもしれない'
    expression = ('私は、' + TARGET + 'を' + predicate + '。' if not focal else
                  '私が' + predicate + 'のは、' + TARGET + 'です。')
    raw = scope + '、\u3000' + expression
    out = checked(raw)
    expected = scope + '、私は' + TARGET + 'を' + predicate + '。'
    assert out.artifact.piece_text == expected
    bound, = out.source_meaning.expression_scopes
    assert raw[slice(*bound.scope_scalar_span)] == scope
    assert raw[slice(*bound.expression_scalar_span)] == expression
    for scalar, utf8 in ((bound.scope_scalar_span, bound.scope_utf8_span),
                         (bound.expression_scalar_span, bound.expression_utf8_span)):
        assert raw[slice(*scalar)].encode('utf-8') == raw.encode('utf-8')[slice(*utf8)]
    assert not out.artifact_plan.declaration_eligible
    assert run(raw, requested_format='declaration').status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('focal', (False, True))
@pytest.mark.parametrize('antecedent_negative', (False, True))
def test_reference_retains_the_same_target_and_both_written_stances(focal, antecedent_negative):
    first_predicate = '大切にしていなかった' if antecedent_negative else '大切にしていた'
    first = '僕は、' + TARGET + 'を' + first_predicate + '。'
    predicate = '大切にしていないかもしれない'
    second = ('僕が' + predicate + 'のは、その時間です。' if focal else
              '僕は、\u3000その時間を' + predicate + '。')
    raw = '🌱を見た。\r\n' + first + second
    out = checked(raw)
    ref, = out.source_meaning.nominal_references
    assert raw[slice(*ref.antecedent_scalar_span)] == TARGET
    assert raw[slice(*ref.reference_scalar_span)] == 'その時間'
    for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                         (ref.reference_scalar_span, ref.reference_utf8_span)):
        assert raw[slice(*scalar)].encode('utf-8') == raw.encode('utf-8')[slice(*utf8)]
    assert first_predicate in out.artifact.piece_text
    assert 'その時間を' + predicate + '。' in out.artifact.piece_text
    assert 'したくない' not in out.artifact.piece_text
    assert not out.artifact_plan.declaration_eligible


def test_state_is_not_negative_wish_affirmation_or_negative_evaluation():
    statements = (
        '私は、' + TARGET + 'を大切にしていない。',
        '私は、' + TARGET + 'を大切にしたくない。',
        '私は、' + TARGET + 'を大切にしている。',
        '私にとって、' + TARGET + 'が大切ではない。',
    )
    artifacts = [checked(s).artifact for s in statements]
    assert [a.piece_text for a in artifacts] == list(statements)
    assert len({a.piece_text_hash for a in artifacts}) == len(statements)
    current, past, modal = _transitive_predicate_forms()
    assert '大切にしていない' in current
    assert '大切にしていませんでした' in past
    assert '大切にしていなかった' in modal
    assert '大切にしていませんでした' not in modal


@pytest.mark.parametrize('sentence', (
    '読書を大切にしていませんでした。',
    '友人は、読書を大切にしていませんでした。',
    '私は、読書を大切にしていませんでしたと聞いた。',
    '私は、読書を大切にしていませんでしたかもしれない。',
    '私は、読書を大切にしていないかもしれないとは限らない。',
    '私は、読書を大切にしていないわけではない。',
    '私は、読書を大切にしていませんでしたか。',
    '私が大切にしていませんでしたのは、読書です。',
    '私は、その時間を大切にしていない。',
    '私は、読書を大切にしていない。友人は、その時間を使った。',
))
def test_new_state_does_not_admit_reports_questions_stacked_modals_or_unbound_references(sentence):
    assert run(sentence + TAIL).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('reference', 'evidence', 'scope', 'plan'))
def test_original_binding_validation_remains_required(mutation):
    raw = ('僕は、' + TARGET + 'を大切にしていなかった。'
           '予定が合うなら、僕は、その時間を大切にしていないかもしれない。')
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
