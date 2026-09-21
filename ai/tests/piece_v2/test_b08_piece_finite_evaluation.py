"""Normal-order evaluations bind to the existing Piece meaning/plan/author.

Synthetic cases only. Technical verification, not human or device acceptance.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest, realize_piece_artifact
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


# Reconcile the previously introduced source-proven adjacent topic omission.
# This changes an old expected body, not the input, source semantics or assertions.

CASES = (
    ('preference',
     '私は一人でゆっくり本を読むことが好きです。まだ、毎日読むとは決めていない。',
     '私は、一人でゆっくり本を読むことが好きです。まだ、毎日読むとは決めていない。'),
    ('negative_past_value',
     '私にとって急いで結論を出すことが必要ではなかったかもしれない。今も同じ考えとは限らない。',
     '私にとって、急いで結論を出すことが必要ではなかったかもしれない。今も同じ考えとは限らない。'),
    ('scoped_role',
     '友人の佐藤さんと昨日は話せなかったので、私にとって急いで結論を出すことが必要ではなかったかもしれない。まだ、答えは決めていない。',
     '友人と昨日は話せなかったので、私にとって、急いで結論を出すことが必要ではなかったかもしれない。まだ、答えは決めていない。'),
    ('condition_preference',
     '落ち着いて過ごせるなら、僕は一人ずつゆっくり話すことが好きです。誰とでも同じように話せるとは限らない。',
     '落ち着いて過ごせるなら、僕は、一人ずつゆっくり話すことが好きです。誰とでも同じように話せるとは限らない。'),
    ('reference_from_value',
     '私にとって家で静かに過ごす時間が必要だったかもしれない。その時間を確保できていたかは、まだ分からない。',
     '私にとって、家で静かに過ごす時間が必要だったかもしれない。その時間を確保できていたかは、まだ分からない。'),
    ('reference_into_condition',
     '私にとって家族と落ち着いて話す時間が大切です。その時間が取れるなら、私は急がずに近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、家族と落ち着いて話す時間が大切です。その時間が取れるなら、急がずに近況を伝えたい。まだ、会う日は決めていない。'),
    ('polite_past',
     '昨日の過ごし方を振り返っている。僕は家で静かに音楽を聴くことが好きでした。今も同じ過ごし方が好きとは限らない。',
     '昨日の過ごし方を振り返っている。僕は、家で静かに音楽を聴くことが好きでした。今も同じ過ごし方が好きとは限らない。'),
    ('contrast',
     '僕はにぎやかな場所で話すことではなく、一人ずつゆっくり話すことが好きだ。人と会いたくないわけではない。',
     '僕は、にぎやかな場所で話すことではなく、一人ずつゆっくり話すことが好きだ。人と会いたくないわけではない。'),
)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-finite-evaluation',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-finite-evaluation', 'v1', text),
        'synthetic-owner', 'synthetic-finite-evaluation', 'v1', **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_normal_order_uses_existing_evaluation_and_complete_author(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert out.source_meaning.personal_evaluations
    assert all(d.operation != 'KEEP_COMPLETE_SOURCE_CONTEXT'
               for d in out.artifact_plan.duties
               if d.node_id in {f.node_id for f in out.source_meaning.personal_evaluations})
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-finite-evaluation', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert candidate == out.artifact.as_candidate()
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression


@pytest.mark.parametrize('ending,polarity,time,commitment', [
    ('です', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('だ', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('だった', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('ではなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('じゃなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('かもしれない', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('だったかもしれない', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('とは限らない', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('じゃなかったとは限らない', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
])
@pytest.mark.parametrize('perspective,base', [('私にとって', '必要'), ('僕は', '好き')])
def test_finite_predicate_original_spans_and_composition(ending, polarity, time, commitment, perspective, base):
    text = '  昨日の予定を振り返るなら、' + perspective + '🌱を眺めて過ごす時間が' + base + ending + '。\r\nまだ、判断できない。  '
    out = generated(text)
    meaning = out.source_meaning
    frame, = meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert text[slice(*frame.scalar_parts[1])] == base + ending
    assert text[slice(*frame.scalar_parts[2])] == '🌱を眺めて過ごす時間'
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    assert out.artifact.piece_text == '昨日の予定を振り返るなら、' + perspective + '、🌱を眺めて過ごす時間が' + base + ending + '。まだ、判断できない。'
    assert len(meaning.expression_scopes) == 1
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('text', [
    '友人は一人で静かに考える時間が好きです。',
    '一人で静かに考える時間が好きです。',
    '私は一人で静かに考える時間が必要です。',
    '私は一人で静かに考える時間は好きです。',
    '私は一人で静かに考える時間も好きです。',
    '私は一人で静かに考える時間が好きだと友人が言った。',
    '私は一人で静かに考える時間が好きではないと思う。',
    '私は一人で静かに考える時間が好きなかもしれない。',
    '私は一人で静かに考える時間が好きだったかもしれないとは限らない。',
    '私はその時間が好きです。',
    '私は佐藤さんと静かに考える時間が好きです。',
    '私は一人で静かに考える時間が好きだった。私は家族と話す時間が好きです。その時間は、まだ取れていない。',
])
def test_no_guessed_author_topic_replacement_report_or_reference(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('field,value', [
    ('polarity', 'AFFIRMATIVE'), ('temporal_scope', 'NONPAST'),
    ('commitment', 'ASSERTED'), ('construction', 'は'),
    ('scalar_parts', ((0, 1), (1, 2), (2, 3))),
    ('utf8_parts', ((0, 1), (1, 2), (2, 3))),
])
def test_finite_frames_remain_derived_from_original_source(field, value):
    out = generated(CASES[1][1])
    meaning = out.source_meaning
    frame, = meaning.personal_evaluations
    bad = replace(meaning, personal_evaluations=(replace(frame, **{field: value}),))
    with pytest.raises(ValueError):
        realize_piece_artifact(bad, out.artifact_plan, tier='free', requested_format=None)


def test_reference_target_and_conditional_intention_remain_in_one_group():
    out = generated(CASES[5][1])
    meaning = out.source_meaning
    ref, = meaning.nominal_references
    frame, = meaning.personal_evaluations
    assert ref.antecedent_scalar_span == frame.scalar_parts[2]
    assert ref.reference_node_id == meaning.expression_scopes[0].node_id
    assert tuple(d.node_id for d in out.artifact_plan.duties) == out.artifact_plan.block_node_ids[0]


@pytest.mark.parametrize('base', ['大切', '大事', '重要', '必要'])
def test_present_explicit_value_preserves_existing_declaration_eligibility(base):
    out = generated('私にとって自分で納得してから考えを伝えることが' + base + 'です。',
                    tier='premium', requested_format='declaration')
    assert out.artifact.format_type == 'declaration'


@pytest.mark.parametrize('text', [
    '私は自分の手で長く使ってきたものが好きです。',
    '私にとって自分の手で長く使ってきたものが大切でした。',
    '私にとって自分の手で長く使ってきたものが必要ではない。',
])
def test_liking_past_or_negative_value_is_not_promoted_to_a_declaration(text):
    generated(text, tier='premium', requested_format='quote')
    out = run(text, tier='premium', requested_format='declaration')
    assert out.status == EngineStatus.UNAVAILABLE


def test_target_internal_subject_does_not_replace_the_experiencer():
    text = '私は家族が自分の言葉でゆっくり話すことが好きです。'
    out = generated(text)
    frame, = out.source_meaning.personal_evaluations
    assert text[slice(*frame.scalar_parts[0])] == '私'
    assert text[slice(*frame.scalar_parts[2])] == '家族が自分の言葉でゆっくり話すこと'
    assert out.artifact.piece_text == '私は、家族が自分の言葉でゆっくり話すことが好きです。'
