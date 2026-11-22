"""Keep an explicit author across a competing topic in a linked condition.

Synthetic regressions for the optional repetition edit; not general Japanese
subject resolution, authentication, native rendering or product acceptance.
"""
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


# Retain the explicit author in its source-written clause, after the other
# participant. No subject is elided and the connective is not reinterpreted.

CASES = (
    ('mother_subject',
     '私にとって家族と話す時間が大切です。その時間を母が取れるなら、私は近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、家族と話す時間が大切です。その時間を母が取れるなら、私は、近況を伝えたい。まだ、会う日は決めていない。'),
    ('mother_topic',
     '私にとって家族と話す時間が大切です。その時間を母は取れないので、私は別の日に近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、家族と話す時間が大切です。その時間を母は取れないので、私は、別の日に近況を伝えたい。まだ、会う日は決めていない。'),
    ('friend_role',
     '私にとって落ち着いて話す時間が大切です。その時間を友人の佐藤さんが取れるなら、私はゆっくり近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、落ち着いて話す時間が大切です。その時間を友人が取れるなら、私は、ゆっくり近況を伝えたい。まだ、会う日は決めていない。'),
    ('different_viewpoint',
     '僕が好きなのは、小さく試して確かめることです。そのことを友人が続けられるなら、僕はそばで学びたい。すぐに答えが出るとは限らない。',
     '僕は、小さく試して確かめることが好きです。そのことを友人が続けられるなら、僕は、そばで学びたい。すぐに答えが出るとは限らない。'),
)


def generated(text):
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-scope-subject',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-input', 'v1', text),
        'synthetic-owner', 'synthetic-input', 'v1'))
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_linked_condition_does_not_transfer_author_to_its_participant(name, text, expected):
    out = generated(text)
    artifact = out.artifact
    assert artifact.piece_text == expected
    assert artifact.body_blocks == (expected,)
    assert artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    meaning = out.source_meaning
    assert meaning.envelope.raw_utf8 == text.encode()
    ref, = meaning.nominal_references
    scope, = meaning.expression_scopes
    assert ref.reference_node_id == scope.node_id
    assert ref.reference_scalar_span[0] == scope.scope_scalar_span[0]
    assert text[slice(*scope.scope_scalar_span)].endswith(scope.marker)
    for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                         (scope.expression_scalar_span, scope.expression_utf8_span)):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-input', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert candidate == artifact.as_candidate()
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば'])
def test_literal_author_and_connective_survive_competing_subject(speaker, marker):
    text = (speaker + 'にとって落ち着いて話す時間が必要かもしれない。'
            + 'その時間を友人が取れる' + marker + '、' + speaker
            + 'は答えを急がずに考えたい。まだ、決めていない。')
    out = generated(text)
    expected = (speaker + 'にとって、落ち着いて話す時間が必要かもしれない。'
                + 'その時間を友人が取れる' + marker + '、' + speaker
                + 'は、答えを急がずに考えたい。まだ、決めていない。')
    assert out.artifact.piece_text == expected
    assert out.source_meaning.expression_scopes[0].marker == marker


@pytest.mark.parametrize('particle', ['が', 'は'])
def test_reference_own_topic_does_not_disable_simple_continuation(particle):
    text = ('私にとって家族と話す時間が大切です。その時間' + particle
            + '取れるなら、私は急がずに近況を伝えたい。まだ、会う日は決めていない。')
    expected = ('私にとって、家族と話す時間が大切です。その時間' + particle
                + '取れるなら、急がずに近況を伝えたい。まだ、会う日は決めていない。')
    assert generated(text).artifact.piece_text == expected


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_retained_author_reaches_existing_b9_without_a_second_text(ratio):
    class Metrics:
        profile_id = 'synthetic-scope-subject-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8,
                                   len(text)*font_px, font_px*.2, True)
    candidate = generated(CASES[0][1]).artifact.as_candidate()
    validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'],
                                candidate['piece_text_hash'])
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(line['text'] for line in layout['lines']) == CASES[0][2]
