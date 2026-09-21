"""Compose source-written polarity/time under a modal without new vocabulary."""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest, realize_piece_artifact
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


# Synthetic source/body pairs, not private records or human product acceptance.
CASES = (
    ('negative_possible_value',
     '私にとって必要ではないかもしれないのは、すぐに答えを出すことです。まだ、自分でもよく分からない。',
     '私にとって、すぐに答えを出すことが必要ではないかもしれない。まだ、自分でもよく分からない。'),
    ('past_possible_preference',
     '昨日の過ごし方を振り返っている。僕が好きだったかもしれないのは、一人で静かに考えることだ。今も同じ気持ちとは限らない。',
     '昨日の過ごし方を振り返っている。僕は、一人で静かに考えることが好きだったかもしれない。今も同じ気持ちとは限らない。'),
    ('reason_negative_past',
     '友人の佐藤さんと昨日は話せなかったので、私にとって必要ではなかったかもしれないのは、急いで結論を出すことです。まだ、答えは決めていない。',
     '友人と昨日は話せなかったので、私にとって、急いで結論を出すことが必要ではなかったかもしれない。まだ、答えは決めていない。'),
    ('conditional_past',
     '昨日の予定を振り返るなら、私にとって必要だったかもしれないのは、一人で考えを整理する時間です。まだ、はっきりとは分からない。',
     '昨日の予定を振り返るなら、私にとって、一人で考えを整理する時間が必要だったかもしれない。まだ、はっきりとは分からない。'),
    ('reference_into_condition',
     '私が望んでいるのは、家族と落ち着いて話す時間です。その時間が取れるなら、私にとって必要ではないかもしれないのは、すぐに返事を決めることです。まだ、結論は決めていない。',
     '私は、家族と落ち着いて話す時間を望んでいる。その時間が取れるなら、私にとって、すぐに返事を決めることが必要ではないかもしれない。まだ、結論は決めていない。'),
    ('reference_from_past_target',
     '私にとって必要だったかもしれないのは、家で静かに過ごす時間です。その時間を確保できていたかは、まだ分からない。',
     '私にとって、家で静かに過ごす時間が必要だったかもしれない。その時間を確保できていたかは、まだ分からない。'),
    ('past_nonuniversal_contrast',
     '僕が好きだったとは限らないのは、早く答えることより、小さく試して確かめることです。今はまだ判断できない。',
     '僕は、早く答えることより、小さく試して確かめることが好きだったとは限らない。今はまだ判断できない。'),
    ('negative_under_nonuniversal',
     '私にとって大切じゃなかったとは限らないのは、家族とゆっくり話す時間だ。まだ、自分でもよく分からない。',
     '私にとって、家族とゆっくり話す時間が大切じゃなかったとは限らない。まだ、自分でもよく分からない。'),
)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-evaluation-composition',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-evaluation-composition', 'v1', text),
        'synthetic-owner', 'synthetic-evaluation-composition', 'v1', **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_composition_flows_through_existing_source_plan_and_author(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-evaluation-composition', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert candidate == out.artifact.as_candidate()
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert out.automatic_progression is False


@pytest.mark.parametrize('state,polarity,time', [
    ('ではない', 'NEGATIVE', 'NONPAST'), ('ではなかった', 'NEGATIVE', 'PAST'),
    ('じゃない', 'NEGATIVE', 'NONPAST'), ('じゃなかった', 'NEGATIVE', 'PAST'),
    ('だった', 'AFFIRMATIVE', 'PAST'),
])
@pytest.mark.parametrize('modal,commitment', [
    ('かもしれない', 'POSSIBLE'), ('とは限らない', 'NON_UNIVERSAL'),
])
@pytest.mark.parametrize('prefix', ['', '昨日のことを振り返るなら、'])
def test_modal_does_not_erase_the_inner_polarity_or_time(state, polarity, time, modal, commitment, prefix):
    predicate = '必要' + state + modal
    text = '  ' + prefix + '私にとって' + predicate + 'のは、🌱を眺めて過ごす時間です。\r\nまだ、判断できない。  '
    out = generated(text)
    meaning = out.source_meaning
    frame, = meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert text[slice(*frame.scalar_parts[1])] == predicate
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    assert out.artifact.piece_text == prefix + '私にとって、🌱を眺めて過ごす時間が' + predicate + '。まだ、判断できない。'
    assert len(meaning.expression_scopes) == bool(prefix)
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('ending', [
    'なのは、一人で考えを整理する時間です。',
    'ではないのは、一人で考えを整理する時間です。',
    'ではなかったのは、一人で考えを整理する時間です。',
    'じゃないのは、一人で考えを整理する時間です。',
    'じゃなかったのは、一人で考えを整理する時間です。',
    'だったのは、一人で考えを整理する時間です。',
    'かもしれないのは、一人で考えを整理する時間です。',
    'とは限らないのは、一人で考えを整理する時間です。',
])
def test_predecessor_simple_evaluations_remain_available(ending):
    generated('私にとって必要' + ending)


@pytest.mark.parametrize('text', [
    '友人にとって必要だったかもしれないのは、一人で過ごす時間です。',
    '必要だったかもしれないのは、一人で過ごす時間です。',
    '私が必要だったかもしれないのは、一人で過ごす時間です。',
    '私にとって必要だったかもしれないのは、その時間です。',
    '私にとって必要だったかもしれないのは、一人で過ごす時間ではない。',
    '私にとって必要だったかもしれないのは、一人で過ごす時間だと友人が言った。',
    '私にとって必要なかもしれないのは、一人で過ごす時間です。',
    '私にとって必要だったかもしれないとは限らないのは、一人で過ごす時間です。',
    '私にとって必要ではなかっただったのは、一人で過ごす時間です。',
    '私にとって必要だったかもしれないのは、佐藤さんと過ごす時間です。',
])
def test_unmodelled_attribution_denial_and_malformed_composition_do_not_gain_authorship(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('field,value', [('polarity', 'AFFIRMATIVE'), ('temporal_scope', 'NONPAST'), ('commitment', 'ASSERTED')])
def test_source_bound_composition_cannot_be_replaced_by_a_simplified_claim(field, value):
    out = generated(CASES[2][1])
    meaning = out.source_meaning
    frame, = meaning.personal_evaluations
    bad = replace(meaning, personal_evaluations=(replace(frame, **{field: value}),))
    with pytest.raises(ValueError):
        realize_piece_artifact(bad, out.artifact_plan, tier='free', requested_format=None)


def test_past_modal_value_cannot_be_requested_as_a_present_declaration():
    out = run('私にとって必要だったかもしれないのは、家で静かに過ごす時間です。',
              tier='premium', requested_format='declaration')
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
