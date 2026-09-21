"""Source-linked paragraph fluency; synthetic cases, not product acceptance."""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest, realize_piece_artifact
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


CASES = (
    ('family_condition',
     '私にとって家族と落ち着いて話す時間が大切です。その時間が取れるなら、私は急がずに近況を伝えたい。まだ、会う日は決めていない。',
     '私にとって、家族と落ち着いて話す時間が大切です。その時間が取れるなら、急がずに近況を伝えたい。まだ、会う日は決めていない。'),
    ('preference_condition',
     '僕が好きなのは、小さく試して確かめることです。そのことを続けられるなら、僕は焦らずに学びたい。すぐに答えが出るとは限らない。',
     '僕は、小さく試して確かめることが好きです。そのことを続けられるなら、焦らずに学びたい。すぐに答えが出るとは限らない。'),
    ('past_negative_reason',
     '私にとって急いで結論を出すことが必要ではなかったかもしれない。そのことを今も迷っているので、私はすぐに決めたくない。まだ、答えは決めていない。',
     '私にとって、急いで結論を出すことが必要ではなかったかもしれない。そのことを今も迷っているので、すぐに決めたくない。まだ、答えは決めていない。'),
    ('focal_condition',
     '私が望んでいるのは、家で静かに過ごす時間です。その時間が取れるならば、私はゆっくり考えをまとめたい。毎日できるとは限らない。',
     '私は、家で静かに過ごす時間を望んでいる。その時間が取れるならば、ゆっくり考えをまとめたい。毎日できるとは限らない。'),
    ('context_role',
     '今週は予定が重なっていた。私にとって大切なのは、友人の佐藤さんと落ち着いて話す時間です。その時間が取れるなら、私は急がずに気持ちを伝えたい。まだ、会う日は決めていない。',
     '今週は予定が重なっていた。\n\n私にとって、友人と落ち着いて話す時間が大切です。その時間が取れるなら、急がずに気持ちを伝えたい。まだ、会う日は決めていない。'),
    ('polite_wish',
     'わたしにとって家で静かに過ごす時間が必要かもしれない。この時間がまだ足りないので、わたしは答えを急ぎたくないです。まだ、自分でもよく分からない。',
     'わたしにとって、家で静かに過ごす時間が必要かもしれない。この時間がまだ足りないので、答えを急ぎたくないです。まだ、自分でもよく分からない。'),
)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-linked-subject', PieceSourceSnapshot('synthetic-owner', 'synthetic-input', 'v1', text),
        'synthetic-owner', 'synthetic-input', 'v1', **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_linked_continuation_keeps_meaning_without_repeating_author(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert out.source_meaning.envelope.raw_utf8 == text.encode()
    ref, = out.source_meaning.nominal_references
    scope, = out.source_meaning.expression_scopes
    assert ref.reference_node_id == scope.node_id
    assert ref.reference_scalar_span[0] == scope.scope_scalar_span[0]
    assert text[slice(*scope.scope_scalar_span)] + '、' in expected
    assert out.artifact_plan.duties[int(scope.node_id.split('s')[-1])-1].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    c = generate_piece_candidate(PieceSourceSnapshot('synthetic-owner', 'synthetic-input', 'v1', text), authenticated_owner_id='synthetic-owner')
    assert c == out.artifact.as_candidate()
    assert c['production_enabled'] is False and c['record_effect'] == c['quota_effect'] == 0


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば'])
def test_scope_operator_and_literal_speaker_are_source_owned(speaker, marker):
    text = (speaker + 'にとって家族と話す時間が大切です。その時間が取れる' + marker + '、'
            + speaker + 'はゆっくり気持ちを伝えたい。まだ、予定は決めていない。')
    out = generated(text)
    expected = speaker + 'にとって、家族と話す時間が大切です。その時間が取れる' + marker + '、ゆっくり気持ちを伝えたい。まだ、予定は決めていない。'
    assert out.artifact.piece_text == expected
    scope, = out.source_meaning.expression_scopes
    assert scope.marker == marker
    for scalar, utf8 in [(scope.scope_scalar_span, scope.scope_utf8_span), (scope.expression_scalar_span, scope.expression_utf8_span)]:
        assert text[slice(*scalar)] == out.source_meaning.envelope.raw_utf8[slice(*utf8)].decode()


@pytest.mark.parametrize('text,retained', [
    ('私にとって家族と話す時間が大切です。その時間が取れるなら、僕は近況を伝えたい。', '僕は、その時間が取れるなら、近況を伝えたい。'),
    ('私にとって家族と話す時間が大切です。昨日は友人と話した。その時間が取れるなら、私は近況を伝えたい。', '私は、その時間が取れるなら、近況を伝えたい。'),
    ('家で落ち着けるなら、私にとって必要なのは、一人で過ごす時間です。その時間が取れるなら、私は本を読みたい。', '私は、その時間が取れるなら、本を読みたい。'),
    ('私にとって家族と話す時間が大切です。明日の予定が空くなら、私は近況を伝えたい。', '私は、明日の予定が空くなら、近況を伝えたい。'),
    ('私にとって家族と話す時間が大切です。その時間が取れるなら、私にとって必要なのは、お互いの話を聞くことです。', 'その時間が取れるなら、私にとって、お互いの話を聞くことが必要です。'),
    ('私にとって家で過ごす時間が大切です。その時間が取れるなら、私は旅に出る前の鳥みたい。', '私は、その時間が取れるなら、旅に出る前の鳥みたい。'),
    # The existing wish grammar does not disambiguate every みたい ending.
    # Preserve the topic rather than infer whether it is a verb or comparison.
    ('私が望んでいるのは、家で静かに過ごす時間です。その時間が取れるなら、私はゆっくり本を読みたい。', '私は、その時間が取れるなら、ゆっくり本を読みたい。'),
    ('私にとって家族と話す時間が大切です。その時間が取れたら、私は近況を伝えたい。', 'その時間が取れたら、私は近況を伝えたい。'),
    ('私が大切にしたいのは、家で過ごす時間です。その時間はまだ取れていない。私はその時間を毎日少しでも持ちたい。', '私は、その時間を毎日少しでも持ちたい。'),
])
def test_do_not_guess_continuity_across_changed_perspective_context_or_unsupported_scope(text, retained):
    assert retained in generated(text).artifact.piece_text


@pytest.mark.parametrize('field', ['nominal_references', 'personal_evaluations', 'expression_scopes'])
def test_removed_source_bindings_cannot_authorize_continuation(field):
    out = generated(CASES[0][1]); meaning = replace(out.source_meaning, **{field: ()})
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('field', ['scalar_parts', 'utf8_parts'])
def test_mutated_viewpoint_spans_are_rejected(field):
    out = generated(CASES[0][1]); m = out.source_meaning; frame, = m.personal_evaluations
    broken = replace(m, personal_evaluations=(replace(frame, **{field: ((1, 2), *getattr(frame, field)[1:])}),))
    with pytest.raises(ValueError):
        realize_piece_artifact(broken, out.artifact_plan, tier='free', requested_format=None)


class Metrics:
    profile_id = 'synthetic-linked-subject-metrics'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text)*font_px
        return TextMeasurement(width, 0, -font_px*.8, width, font_px*.2, True)


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_exact_canonical_continuation_reaches_existing_visual_contract(ratio):
    out = generated(CASES[0][1]); c = out.artifact.as_candidate()
    validate_piece_text_binding(c['content_payload'], c['piece_text'], c['piece_text_hash'])
    r = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio, theme='soft_paper')
    layout = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    assert ''.join(line['text'] for line in layout['lines']) == ''.join(c['content_payload']['body_blocks'])
    assert c['piece_text'] == CASES[0][2]
