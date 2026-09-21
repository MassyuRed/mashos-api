"""Synthetic personal-value/preference editorial cases; no human acceptance."""
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest, realize_piece_artifact
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


CASES = (
    ('value_comparison',
     '私にとって大切なのは、早く答えることより、自分で納得して選ぶことです。まだ、答えは決めていない。',
     '私にとって、早く答えることより、自分で納得して選ぶことが大切です。まだ、答えは決めていない。'),
    ('preference_contrast',
     '私が好きなのは、にぎやかな場所で話すことではなく、一人ずつゆっくり話すことだ。人と会いたくないわけではない。',
     '私は、にぎやかな場所で話すことではなく、一人ずつゆっくり話すことが好きだ。人と会いたくないわけではない。'),
    ('negative_value',
     '私にとって必要ではないのは、すぐに結論を出すことだ。今は考えを整理する時間を残している。',
     '私にとって、すぐに結論を出すことが必要ではない。今は考えを整理する時間を残している。'),
    ('past_role',
     '私にとって大切だったのは、友人の佐藤さんと毎日話す時間だ。今も同じ頻度で会いたいとは限らない。',
     '私にとって、友人と毎日話す時間が大切だった。今も同じ頻度で会いたいとは限らない。'),
    ('conditional_value',
     '私にとって重要なのは、気持ちに余裕があるときに、家族の話を聞くことだ。余裕がない日は無理をしない。',
     '私にとって、気持ちに余裕があるときに、家族の話を聞くことが重要だ。余裕がない日は無理をしない。'),
    ('context_preference',
     '昨日は答えを急いでしまった。私が苦手なのは、考える間もなく結論を伝えることです。まだ、話す順番は決めていない。',
     '昨日は答えを急いでしまった。私は、考える間もなく結論を伝えることが苦手です。まだ、話す順番は決めていない。'),
    ('tentative_value',
     '私にとって必要かもしれないのは、一人でゆっくり考える時間だ。まだ、自分でもよく分からない。',
     '私にとって、一人でゆっくり考える時間が必要かもしれない。まだ、自分でもよく分からない。'),
    ('value_noun',
     '私にとって大切なのは、対話です。対話が続けば、考えを確かめ直せる。',
     '私にとって、対話が大切です。対話が続けば、考えを確かめ直せる。'),
)


def run(text, *, tier='free', requested_format=None):
    req = PieceGenerationRequest('synthetic-evaluation',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-saved', 'v1', text),
        'synthetic-owner', 'synthetic-saved', 'v1', tier=tier, requested_format=requested_format)
    return MeaningExperienceEngine().generate(req)


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_personal_evaluation_produces_body_without_inventing_a_wish(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.artifact.body_blocks == (expected,)
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert any(d.operation == 'SOURCE_PERSONAL_EVALUATION' for d in out.artifact_plan.duties)
    direct = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-saved', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert direct == out.artifact.as_candidate()
    assert not direct['production_enabled'] and direct['record_effect'] == direct['quota_effect'] == 0


@pytest.mark.parametrize('inflection,finite,polarity,temporal,commitment', [
    ('な', '好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('ではない', '好きではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃない', '好きじゃない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('だった', '好きだった', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではなかった', '好きではなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('じゃなかった', '好きじゃなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('かもしれない', '好きかもしれない', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('とは限らない', '好きとは限らない', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
])
def test_polarity_temporal_scope_and_commitment_are_realized_not_promoted(inflection, finite, polarity, temporal, commitment):
    text = '僕が好き' + inflection + 'のは、家で静かに音楽を聴くことです。'
    out = generated(text, tier='premium')
    assert out.artifact.piece_text == '僕は、家で静かに音楽を聴くことが' + finite + '。'
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, temporal, commitment)
    assert 'declaration' not in out.artifact.eligible_formats


@pytest.mark.parametrize('text', [
    '友人にとって大切なのは、一人でじっくり考える時間です。',
    '大切なのは、一人でじっくり考える時間です。',
    '私が好きなのは、一人でじっくり考える時間だと友人が言った。',
    '私にとって大切なのは、一人でじっくり考える時間だと思われている。',
    '私にとって大切なのは、一人でじっくり考える時間ではない。',
    '私にとって大切なのは、一人でじっくり考える時間かもしれない。',
    '私にとって大切なのは、一人でじっくり考える時間だった。',
    '私にとって大切なのは、その時間です。',
    '私にとって大切なのは、友人が好きなのは一人で過ごすことです。',
    '私にとって大切なのは、友人が音楽だ。',
    '私が必要なのは、一人でじっくり考える時間です。',
    '私は一人で過ごす時間が大切だ。',
    '私はいつか成長する人間だ。',
])
def test_no_generic_replay_reported_viewpoint_or_outer_scope_reinterpretation(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert not out.automatic_progression


@pytest.mark.parametrize('text', [
    '私にとって大切なのは、user@example.com に連絡することだ。',
    '私にとって大切なのは、佐藤さんと落ち着いて話す時間だ。',
    '私にとって大切なのは、友人の佐藤さんと友人の田中さんと話す時間だ。',
])
def test_source_contact_and_role_boundaries_are_not_relaxed(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_original_parts_bind_scalar_and_utf8_before_role_publicization():
    text = '  私にとって大切なのは、🌱を眺めて静かに過ごす時間です。\r\n昨日は時間が取れなかった。  '
    out = generated(text)
    m = out.source_meaning
    frame, = m.personal_evaluations
    parts = []
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
        actual = text[slice(*scalar)]
        assert actual == m.envelope.raw_utf8[slice(*utf8)].decode()
        parts.append(actual)
    assert parts == ['私', '大切な', '🌱を眺めて静かに過ごす時間']
    assert out.artifact.piece_text == '私にとって、🌱を眺めて静かに過ごす時間が大切です。昨日は時間が取れなかった。'


@pytest.mark.parametrize('mutation', ['omit', 'speaker', 'target', 'utf8', 'construction', 'kind', 'polarity', 'temporal', 'commitment', 'copula'])
def test_source_semantics_are_consumed_not_unchecked_metadata(mutation):
    out = generated(CASES[0][1]); m = out.source_meaning; frame, = m.personal_evaluations
    parts = list(frame.scalar_parts)
    if mutation == 'omit': m = replace(m, personal_evaluations=())
    else:
        if mutation == 'speaker': parts[0] = parts[2]; frame = replace(frame, scalar_parts=tuple(parts))
        if mutation == 'target': parts[2] = (0, 1); frame = replace(frame, scalar_parts=tuple(parts))
        if mutation == 'utf8': frame = replace(frame, utf8_parts=((0, 1), *frame.utf8_parts[1:]))
        if mutation == 'construction': frame = replace(frame, construction='が')
        if mutation == 'kind': frame = replace(frame, kind='PERSONAL_PREFERENCE')
        if mutation == 'polarity': frame = replace(frame, polarity='NEGATIVE')
        if mutation == 'temporal': frame = replace(frame, temporal_scope='PAST')
        if mutation == 'commitment': frame = replace(frame, commitment='POSSIBLE')
        if mutation == 'copula': frame = replace(frame, copula='だ')
        m = replace(m, personal_evaluations=(frame,))
    with pytest.raises(ValueError):
        realize_piece_artifact(m, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('fmt', ['quote', 'declaration'])
def test_qualification_cannot_be_cut_for_a_standalone_format(fmt):
    out = run(CASES[0][1], tier='premium', requested_format=fmt)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_explicit_current_value_but_not_preference_is_eligible_for_declaration():
    value = generated('私にとって大切なのは、自分で納得して選ぶことだ。', tier='premium', requested_format='declaration')
    assert value.artifact.format_type == 'declaration'
    preference = run('私が好きなのは、家で静かに音楽を聴くことだ。', tier='premium', requested_format='declaration')
    assert preference.status == EngineStatus.UNAVAILABLE
    quote = generated('私が好きなのは、家で静かに音楽を聴くことだ。', tier='premium', requested_format='quote')
    assert quote.artifact.format_type == 'quote'


def test_evaluation_and_wish_do_not_detach_the_context_or_drop_repetition():
    text = ('昨日は友人の佐藤さんと話した。私が好きなのは、ゆっくり話を聞くことだ。'
            'まだ予定は決めていない。まだ予定は決めていない。'
            '私は気持ちが整理できたら、また話したい。')
    out = generated(text)
    assert out.artifact.body_blocks == (
        '昨日は友人と話した。私は、ゆっくり話を聞くことが好きだ。'
        'まだ予定は決めていない。まだ予定は決めていない。私は、気持ちが整理できたら、また話したい。',)
    assert len(out.source_meaning.graph.nodes) == 5
    for private in ('佐藤', 'synthetic-owner', 'synthetic-saved'):
        assert private not in json.dumps(out.as_body_free(), ensure_ascii=False) + repr(out.source_meaning.personal_evaluations)


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_actual_canonical_evaluation_body_is_the_b9_layout_body(ratio):
    class Metrics:
        profile_id = 'synthetic-evaluation-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    c = generated(CASES[3][1]).artifact.as_candidate()
    recipe = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(row['text'] for row in layout['lines']) == c['piece_text']


def test_existing_free_short_essay_minimum_is_not_relaxed_for_preferences():
    text = '僕が好きなのは、家で静かに音楽を聴くことです。'
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.reason_codes == ('format_not_eligible',)
    assert generated(text, tier='premium').artifact.format_type == 'quote'


@pytest.mark.parametrize('text', [
    '私が好きなのは、東京大学教授です。',
    '僕が苦手だったのは、親戚一同です。',
])
def test_bare_person_like_nominals_do_not_infer_experiencer_ownership(text):
    out = run(text, tier='premium')
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
