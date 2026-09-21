"""A written concession keeps both sides; it is not a reason or a condition.

Synthetic integration examples for the existing disabled CMEE Piece path.
No public API, source retrieval, native export or human acceptance is claimed.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


# All reference-bound premises keep the written topic position. Concessions
# and optional omission are unchanged; reasons/conditions retain the same author.

CASES = (
    ('uncertain_wish',
     'まだ自信はないけれど、私は小さく試して確かめたい。すぐに結果が出るとは限らない。',
     'まだ自信はないけれど、私は、小さく試して確かめたい。すぐに結果が出るとは限らない。'),
    ('negative_wish',
     '話す時間は楽しいけれども、僕は疲れたまま話を続けたくない。相手との時間が嫌いなわけではない。',
     '話す時間は楽しいけれども、僕は、疲れたまま話を続けたくない。相手との時間が嫌いなわけではない。'),
    ('role_and_reservation',
     '友人の佐藤さんは忙しいけれど、私は無理のない日にゆっくり話したい。まだ、会う日は決めていない。',
     '友人は忙しいけれど、私は、無理のない日にゆっくり話したい。まだ、会う日は決めていない。'),
    ('value_with_context',
     '今週は予定が重なっていた。短い時間しか取れないけれど、私にとって大切なのは、家族の話を最後まで聞くことです。毎日できるとは限らない。',
     '今週は予定が重なっていた。短い時間しか取れないけれど、私にとって、家族の話を最後まで聞くことが大切です。毎日できるとは限らない。'),
    ('past_negative_possible',
     '昨日は落ち着かなかったけれども、私にとって急いで結論を出すことが必要ではなかったかもしれない。今も同じ考えとは限らない。',
     '昨日は落ち着かなかったけれども、私にとって、急いで結論を出すことが必要ではなかったかもしれない。今も同じ考えとは限らない。'),
    ('tentative_preference',
     '答えはまだ出ていないけれど、僕が好きだったかもしれないのは、小さく試して確かめることです。今も同じ気持ちとは限らない。',
     '答えはまだ出ていないけれど、僕は、小さく試して確かめることが好きだったかもしれない。今も同じ気持ちとは限らない。'),
    ('reference_from_value',
     '予定はまだ決まらないけれど、私にとって必要なのは、家で静かに過ごす時間です。その時間を確保できるかは、まだ分からない。',
     '予定はまだ決まらないけれど、私にとって、家で静かに過ごす時間が必要です。その時間を確保できるかは、まだ分からない。'),
    ('linked_reference',
     '私にとって家族と落ち着いて話す時間が大切です。その時間が取れないけれど、私は急いで返事を決めたくない。まだ、日程は決めていない。',
     '私にとって、家族と落ち着いて話す時間が大切です。その時間が取れないけれど、急いで返事を決めたくない。まだ、日程は決めていない。'),
    ('reference_other_subject',
     '私にとって家族と落ち着いて話す時間が大切です。その時間を家族が取れないけれど、私は近況を伝える方法を考えたい。まだ、方法は決めていない。',
     '私にとって、家族と落ち着いて話す時間が大切です。その時間を家族が取れないけれど、私は、近況を伝える方法を考えたい。まだ、方法は決めていない。'),
    ('previous_unsupported_intention',
     '時間が少ないけれど、私は急がずに自分の答えを考えたい。',
     '時間が少ないけれど、私は、急がずに自分の答えを考えたい。'),
    ('previous_unsupported_value',
     '落ち着いて過ごせるけれど、私にとって大切なのは、一人で過ごす時間です。',
     '落ち着いて過ごせるけれど、私にとって、一人で過ごす時間が大切です。'),
    ('finite_nominal_preference',
     '時間は短いけれど、私は読書が好きです。長い本を読みたいわけではない。',
     '時間は短いけれど、私は、読書が好きです。長い本を読みたいわけではない。'),
    ('finite_nominal_past_possible',
     '昨日は楽しかったけれど、僕は雑談が苦手だったかもしれない。今も同じ気持ちとは限らない。',
     '昨日は楽しかったけれど、僕は、雑談が苦手だったかもしれない。今も同じ気持ちとは限らない。'),
    ('finite_nominal_negative_nonuniversal',
     '結果は出たけれども、わたしは競争が苦手じゃなかったとは限らない。まだ、自分でもよく分からない。',
     '結果は出たけれども、わたしは、競争が苦手じゃなかったとは限らない。まだ、自分でもよく分からない。'),
    ('finite_nominal_distinct_subject',
     '友人の佐藤さんはコーヒーが好きだけれど、私は紅茶が好きです。同じものを選びたいわけではない。',
     '友人はコーヒーが好きだけれど、私は、紅茶が好きです。同じものを選びたいわけではない。'),
    ('reference_additive_subject',
     '私にとって家族と落ち着いて話す時間が大切です。その時間を家族も取れないけれど、私は近況を伝える方法を考えたい。まだ、方法は決めていない。',
     '私にとって、家族と落ち着いて話す時間が大切です。その時間を家族も取れないけれど、私は、近況を伝える方法を考えたい。まだ、方法は決めていない。'),
)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-concession',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-concession', 'v1', text),
        'synthetic-owner', 'synthetic-concession', 'v1', **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_complete_concession_flows_from_source_to_existing_b8(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == 'SOURCE_EXPLICIT_CONCESSION'
    assert scope.marker in ('けれど', 'けれども')
    node = next(n for n in out.source_meaning.graph.nodes if n.node_id == scope.node_id)
    assert node.node_kind == 'PIECE_SOURCE_CONCESSION_SCOPED_EXPRESSION'
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-concession', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert candidate == out.artifact.as_candidate()
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression


@pytest.mark.parametrize('marker', ['けれど', 'けれども'])
@pytest.mark.parametrize('speaker', ['私', '僕', 'わたし'])
def test_source_ranges_and_speaker_are_not_reconstructed_from_labels(marker, speaker):
    text = '  🌱を見てもまだ迷っている' + marker + '、' + speaker + 'は焦らずに考えたい。\r\nまだ、答えは決めていない。  '
    out = generated(text)
    meaning = out.source_meaning
    scope, = meaning.expression_scopes
    assert scope.relation == 'SOURCE_EXPLICIT_CONCESSION'
    for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                         (scope.expression_scalar_span, scope.expression_utf8_span)):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    assert text[slice(*scope.expression_scalar_span)] == speaker + 'は焦らずに考えたい。'
    assert out.artifact.piece_text == ('🌱を見てもまだ迷っている' + marker + '、'
        + speaker + 'は、焦らずに考えたい。まだ、答えは決めていない。')


@pytest.mark.parametrize('case_index,polarity,temporal,commitment', [
    (3, 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    (4, 'NEGATIVE', 'PAST', 'POSSIBLE'),
    (5, 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
])
def test_concession_does_not_rewrite_the_evaluation(case_index, polarity, temporal, commitment):
    out = generated(CASES[case_index][1])
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, temporal, commitment)
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
        assert CASES[case_index][1][slice(*scalar)] == out.source_meaning.envelope.raw_utf8[slice(*utf8)].decode()


@pytest.mark.parametrize('marker,relation,kind', [
    ('ので', 'SOURCE_EXPLICIT_REASON', 'PIECE_SOURCE_REASON_SCOPED_EXPRESSION'),
    ('なら', 'SOURCE_EXPLICIT_CONDITION', 'PIECE_SOURCE_CONDITION_SCOPED_EXPRESSION'),
    ('ならば', 'SOURCE_EXPLICIT_CONDITION', 'PIECE_SOURCE_CONDITION_SCOPED_EXPRESSION'),
])
def test_predecessor_reason_and_condition_retain_their_kind_and_author(marker, relation, kind):
    text = 'まだ気持ちが落ち着かない' + marker + '、私は答えを急ぎたくない。'
    out = generated(text)
    scope, = out.source_meaning.expression_scopes
    assert (scope.marker, scope.relation) == (marker, relation)
    assert out.source_meaning.graph.nodes[0].node_kind == kind
    assert out.artifact.piece_text == '私は、まだ気持ちが落ち着かない' + marker + '、答えを急ぎたくない。'


@pytest.mark.parametrize('text', [
    'まだ迷っている、私は小さく試して確かめたい。',
    'まだ迷っているのに、私は小さく試して確かめたい。',
    'まだ迷っているが、私は小さく試して確かめたい。',
    'まだ迷っているけれど、友人は小さく試して確かめたい。',
    'まだ迷っているけれど、小さく試して確かめたい。',
    'まだ迷っているけれど、私は小さく試して確かめたいと友人が言った。',
    'まだ迷っているけれど、私にとってその時間が大切です。',
    '友人の佐藤さんは忙しいけれど、山田さんは明日話したい。',
])
def test_unmarked_or_unresolved_attribution_is_not_given_to_the_author(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('field,value', [
    ('relation', 'SOURCE_EXPLICIT_REASON'),
    ('relation', 'SOURCE_EXPLICIT_CONDITION'),
    ('marker', 'ので'),
    ('scope_scalar_span', (0, 1)),
])
def test_written_relation_cannot_be_relabelled_without_its_source(field, value):
    out = generated(CASES[0][1])
    meaning = out.source_meaning
    scope, = meaning.expression_scopes
    bad = replace(meaning, expression_scopes=(replace(scope, **{field: value}),))
    with pytest.raises(ValueError):
        realize_piece_artifact(bad, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('format_type', ['quote', 'declaration'])
def test_concession_is_not_excerpted_or_promoted_to_unconditional_pledge(format_type):
    out = run('まだ迷っているけれど、私は小さく試して確かめたい。',
              tier='premium', requested_format=format_type)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば', 'けれど', 'けれども'])
def test_additive_participant_does_not_inherit_the_authors_wish(marker):
    prefix = '私にとって家族と落ち着いて話す時間が大切です。'
    premise = 'その時間を家族も取れない' + marker
    text = prefix + premise + '、私は近況を伝える方法を考えたい。まだ、方法は決めていない。'
    out = generated(text)
    stance = '近況を伝える方法を考えたい。まだ、方法は決めていない。'
    joined = premise + '、私は、'
    expected = '私にとって、家族と落ち着いて話す時間が大切です。' + joined + stance
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    scope, = out.source_meaning.expression_scopes
    assert text[slice(*scope.scope_scalar_span)] == premise
    assert text[slice(*scope.expression_scalar_span)] == '私は近況を伝える方法を考えたい。'
    assert out.artifact.eligible_formats == ('short_essay',)


@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば', 'けれど', 'けれども'])
def test_referents_own_additive_particle_is_not_a_new_participant(marker):
    prefix = '私にとって家族と落ち着いて話す時間が大切です。'
    premise = 'その時間も取れない' + marker
    text = prefix + premise + '、私は答えを急ぎたくない。'
    out = generated(text)
    expected = '私にとって、家族と落ち着いて話す時間が大切です。' + premise + '、答えを急ぎたくない。'
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.source_meaning.envelope.raw_utf8.decode() == text
