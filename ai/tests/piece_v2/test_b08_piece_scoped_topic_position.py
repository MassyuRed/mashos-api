"""Keep a retained first-person topic in its source-written scoped clause.

Synthetic source/author/B9 regressions. The optional topic omission is still
owned by the existing continuation check; no new subject inference is made.
"""
from dataclasses import asdict
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe


CASES = (
    ('other_subject',
     '私にとって家族と話す時間が大切です。その時間を母が取れるなら、私は近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、家族と話す時間が大切です。その時間を母が取れるなら、私は、近況を伝えたい。まだ、会う日は決めていない。'),
    ('negative_reason',
     '私にとって家族と話す時間が大切です。その時間を母は取れないので、私は別の日に近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、家族と話す時間が大切です。その時間を母は取れないので、私は、別の日に近況を伝えたい。まだ、会う日は決めていない。'),
    ('additive_participant',
     '僕が好きなのは、小さく試して確かめることです。そのことを友人も続けられるならば、僕はそばで学びたい。すぐに答えが出るとは限らない。',
     '僕は、小さく試して確かめることが好きです。そのことを友人も続けられるならば、僕は、そばで学びたい。すぐに答えが出るとは限らない。'),
    ('role_publicization',
     '私にとって落ち着いて話す時間が大切です。その時間を友人の佐藤さんが取れるなら、私はゆっくり近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、落ち着いて話す時間が大切です。その時間を友人が取れるなら、私は、ゆっくり近況を伝えたい。まだ、会う日は決めていない。'),
    ('changed_literal_viewpoint',
     '私にとって家族と話す時間が大切です。その時間が取れるなら、僕は近況を伝えたい。',
     '私にとって、家族と話す時間が大切です。その時間が取れるなら、僕は、近況を伝えたい。'),
    ('intervening_context',
     '私にとって家族と話す時間が大切です。昨日は友人と話した。その時間が取れるなら、私は近況を伝えたい。',
     '私にとって、家族と話す時間が大切です。昨日は友人と話した。その時間が取れるなら、私は、近況を伝えたい。'),
    ('past_negative_possible',
     '私にとって急いで結論を出すことが必要ではなかったかもしれない。そのことを今も迷っているので、私はすぐに決めたくない。まだ、答えは決めていない。',
     '私にとって、急いで結論を出すことが必要ではなかったかもしれない。そのことを今も迷っているので、私は、すぐに決めたくない。まだ、答えは決めていない。'),
    ('comparison_not_wish',
     '私にとって家で過ごす時間が大切です。その時間が取れるなら、私は旅に出る前の鳥みたい。',
     '私にとって、家で過ごす時間が大切です。その時間が取れるなら、私は、旅に出る前の鳥みたい。'),
)


def generated(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-topic-position', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-topic-position', source, source.owner_id, source.saved_input_id, source.source_version))
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return source, out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_retained_topic_does_not_move_in_front_of_its_referential_scope(name, text, expected):
    source, out = generated(text)
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not plan.declaration_eligible
    scope, = meaning.expression_scopes
    reference, = meaning.nominal_references
    assert reference.reference_node_id == scope.node_id
    assert reference.reference_scalar_span[0] == scope.scope_scalar_span[0]
    for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                         (scope.expression_scalar_span, scope.expression_utf8_span)):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode('utf-8')
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert before == (asdict(meaning), asdict(plan))
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば', 'けれど', 'けれども'])
def test_exact_operator_and_additive_participant_keep_written_clause_order(marker):
    source = ('わたしにとって落ち着いて話す時間が必要かもしれない。'
              'その時間を家族も取れる' + marker + '、わたしは答えを急がずに考えたい。まだ、決めていない。')
    _, out = generated(source)
    expected = ('わたしにとって、落ち着いて話す時間が必要かもしれない。'
                'その時間を家族も取れる' + marker + '、わたしは、答えを急がずに考えたい。まだ、決めていない。')
    assert out.artifact.piece_text == expected
    assert out.source_meaning.expression_scopes[0].marker == marker


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_same_canonical_topic_position_is_consumed_by_b9(ratio):
    class Metrics:
        profile_id = 'synthetic-topic-position-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2, True)
    _, out = generated(CASES[1][1])
    candidate = out.artifact.as_candidate()
    validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'], candidate['piece_text_hash'])
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(line['text'] for line in layout['lines']) == CASES[1][2]


def test_proven_optional_omission_and_nonreferential_scope_are_unchanged():
    _, linked = generated('私にとって家族と話す時間が大切です。その時間が取れるなら、私は近況を伝えたい。')
    assert linked.artifact.piece_text == '私にとって、家族と話す時間が大切です。その時間が取れるなら、近況を伝えたい。'
    _, unlinked = generated('集中できる時間が少ないので、私は朝の予定を少し減らしたい。')
    assert unlinked.artifact.piece_text == '私は、集中できる時間が少ないので、朝の予定を少し減らしたい。'
