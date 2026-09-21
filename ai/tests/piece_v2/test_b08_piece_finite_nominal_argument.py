"""Explicit self-topic nominal preferences; synthetic inputs, not product acceptance."""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe


CASES = (
    ('reading', '私は読書が好きです。読む本は、気分に合わせて自分で選びたい。',
     '私は、読書が好きです。読む本は、気分に合わせて自分で選びたい。',
     '私', '読書', '好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('coffee', '僕はコーヒーが好きです。毎日飲みたいわけではなく、自分の気分に合わせて楽しみたい。',
     '僕は、コーヒーが好きです。毎日飲みたいわけではなく、自分の気分に合わせて楽しみたい。',
     '僕', 'コーヒー', '好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('past_possible', 'わたしは競争が苦手だったかもしれない。今も同じ気持ちとは限らない。',
     'わたしは、競争が苦手だったかもしれない。今も同じ気持ちとは限らない。',
     'わたし', '競争', '苦手だったかもしれない', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('negative', '俺は雑談が苦手ではない。いつでも誰とでも話したいわけではない。',
     '俺は、雑談が苦手ではない。いつでも誰とでも話したいわけではない。',
     '俺', '雑談', '苦手ではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('condition', '落ち着いて過ごせるなら、私は散歩が好きです。長い距離を歩きたいわけではない。',
     '落ち着いて過ごせるなら、私は、散歩が好きです。長い距離を歩きたいわけではない。',
     '私', '散歩', '好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('polite_past', '昨日の過ごし方を振り返るなら、ぼくは読書が好きでした。今も同じ過ごし方が好きとは限らない。',
     '昨日の過ごし方を振り返るなら、ぼくは、読書が好きでした。今も同じ過ごし方が好きとは限らない。',
     'ぼく', '読書', '好きでした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('person_target', '私は友人が好きです。いつも会いたいわけではなく、一人で過ごす時間も残したい。',
     '私は、友人が好きです。いつも会いたいわけではなく、一人で過ごす時間も残したい。',
     '私', '友人', '好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('negative_nonuniversal', 'おれは競争が苦手じゃなかったとは限らない。まだ、自分でもよく分からない。',
     'おれは、競争が苦手じゃなかったとは限らない。まだ、自分でもよく分からない。',
     'おれ', '競争', '苦手じゃなかったとは限らない', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
)


def run(text, **changes):
    request = PieceGenerationRequest('synthetic-nominal',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-saved', 'v1', text),
        'synthetic-owner', 'synthetic-saved', 'v1')
    return MeaningExperienceEngine().generate(replace(request, **changes))


def generated(text, **changes):
    out = run(text, **changes)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact is not None
    return out


@pytest.mark.parametrize('name,text,expected,speaker,target,predicate,polarity,time,commitment', CASES)
def test_nominal_argument_reaches_existing_plan_author_and_b8(
        name, text, expected, speaker, target, predicate, polarity, time, commitment):
    out = generated(text)
    frame, = out.source_meaning.personal_evaluations
    assert frame.kind == 'PERSONAL_PREFERENCE' and frame.construction == 'は'
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert [text[slice(*span)] for span in frame.scalar_parts] == [speaker, predicate, target]
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
        assert text[slice(*scalar)] == out.source_meaning.envelope.raw_utf8[slice(*utf8)].decode()
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert out.artifact.piece_text == expected and out.artifact.body_blocks == (expected,)
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert out.artifact_plan.block_node_ids == (tuple(n.node_id for n in out.source_meaning.graph.nodes),)
    assert all(d.operation != 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in out.artifact_plan.duties
               if d.node_id == frame.node_id)
    direct = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-saved', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert direct == out.artifact.as_candidate()
    assert direct['record_effect'] == direct['quota_effect'] == 0
    assert not direct['production_enabled'] and not out.automatic_progression


@pytest.mark.parametrize('text', [
    '私が好きなのは、東京大学教授です。',
    '僕が苦手だったのは、親戚一同です。',
    '私が好きなのは、読書です。',
    '僕がコーヒーが好きです。',
    '友人はコーヒーが好きです。',
    'コーヒーが好きです。',
    '私はコーヒーは好きです。',
    '私はコーヒーも好きです。',
    '私はコーヒーが必要です。',
    '私はコーヒーが好きだと友人が言った。',
    '私はあれが好きです。',
    '私は佐藤さんが好きです。',
    '私はuser@example.comが好きです。',
    '僕はコーヒーが好きです。毎日飲みたいわけではなく、その日の気分に合わせて楽しみたい。',
])
def test_nominal_admission_does_not_guess_an_experiencer_or_relax_other_boundaries(text):
    out = run(text, tier='premium')
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('field,value', [
    ('construction', 'が'), ('kind', 'PERSONAL_VALUE'),
    ('polarity', 'NEGATIVE'), ('temporal_scope', 'PAST'),
    ('scalar_parts', ((0, 1), (1, 2), (2, 3))),
    ('utf8_parts', ((0, 1), (1, 2), (2, 3))),
])
def test_nominal_frame_cannot_be_replaced_by_unverified_metadata(field, value):
    out = generated(CASES[0][1])
    frame, = out.source_meaning.personal_evaluations
    meaning = replace(out.source_meaning,
                      personal_evaluations=(replace(frame, **{field: value}),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, out.artifact_plan, tier='free', requested_format=None)


def test_short_preference_does_not_lower_the_free_minimum_or_become_a_declaration():
    text = '僕はコーヒーが好きです。'
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.reason_codes == ('format_not_eligible',)
    assert generated(text, tier='premium', requested_format='quote').artifact.piece_text == '僕は、コーヒーが好きです。'
    assert run(text, tier='premium', requested_format='declaration').status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_nominal_preference_uses_the_same_complete_canonical_body_in_b9(ratio):
    class Metrics:
        profile_id = 'synthetic-nominal-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    c = generated(CASES[1][1]).artifact.as_candidate()
    recipe = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(line['text'] for line in layout['lines']) == c['piece_text']
    assert not layout['clipped'] and not layout['missing_glyph']
