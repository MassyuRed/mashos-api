"""Source clauses qualify an existing evaluation frame, not a new user intention."""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


# Public synthetic inputs; none is a claim of user or human acceptance.
CASES = (
    ('reason_value',
     '答えを急ぐと気持ちが追いつかないので、私にとって大切なのは、自分で納得して選ぶことです。まだ、結論は決めていない。',
     '答えを急ぐと気持ちが追いつかないので、私にとって、自分で納得して選ぶことが大切です。まだ、結論は決めていない。'),
    ('condition_preference',
     '落ち着いて過ごせるなら、私が好きなのは、一人ずつゆっくり話すことです。誰とでも同じように話せるとは限らない。',
     '落ち着いて過ごせるなら、私は、一人ずつゆっくり話すことが好きです。誰とでも同じように話せるとは限らない。'),
    ('past_negative_reason',
     '友人の佐藤さんと昨日は話せなかったので、私にとって必要ではなかったのは、すぐに結論を出すことだ。今も同じ考えとは限らない。',
     '友人と昨日は話せなかったので、私にとって、すぐに結論を出すことが必要ではなかった。今も同じ考えとは限らない。'),
    ('tentative_condition',
     '気持ちに余裕がないなら、私にとって必要かもしれないのは、一人で考えを整理する時間です。まだ、自分でもよく分からない。',
     '気持ちに余裕がないなら、私にとって、一人で考えを整理する時間が必要かもしれない。まだ、自分でもよく分からない。'),
    ('reference_into_evaluation_scope',
     '私が望んでいるのは、家族と落ち着いて話す時間です。その時間が取れるなら、私にとって大切なのは、お互いの話を最後まで聞くことです。まだ、予定は決めていない。',
     '私は、家族と落ち着いて話す時間を望んでいる。その時間が取れるなら、私にとって、お互いの話を最後まで聞くことが大切です。まだ、予定は決めていない。'),
    ('reference_from_scoped_target',
     '慌ただしい日が続いているので、私にとって必要なのは、家で静かに過ごす時間です。その時間を確保できるかは、まだ分からない。',
     '慌ただしい日が続いているので、私にとって、家で静かに過ごす時間が必要です。その時間を確保できるかは、まだ分からない。'),
    ('contrast_with_conditional_preference',
     '一人で決められるならば、僕が好きなのは、早く答えることより、小さく試して確かめることです。すぐに正解が分かるわけではない。',
     '一人で決められるならば、僕は、早く答えることより、小さく試して確かめることが好きです。すぐに正解が分かるわけではない。'),
    ('past_preference_and_context',
     '昨日は予定が重なっていた。慌ただしい日が続いていたので、僕が好きだったのは、家で静かに音楽を聴くことだ。今も同じ過ごし方が好きとは限らない。',
     '昨日は予定が重なっていた。慌ただしい日が続いていたので、僕は、家で静かに音楽を聴くことが好きだった。今も同じ過ごし方が好きとは限らない。'),
)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-scoped-evaluation',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-scoped-evaluation', 'v1', text),
        'synthetic-owner', 'synthetic-scoped-evaluation', 'v1', **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_scoped_value_or_preference_keeps_the_entire_source_relation(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    scope, = out.source_meaning.expression_scopes
    frame, = out.source_meaning.personal_evaluations
    assert scope.node_id == frame.node_id
    assert any(d.node_id == frame.node_id and d.operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
               for d in out.artifact_plan.duties)
    direct = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-scoped-evaluation', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert direct == out.artifact.as_candidate()
    assert not direct['production_enabled']
    assert direct['record_effect'] == direct['quota_effect'] == 0


@pytest.mark.parametrize('marker,relation', [
    ('ので', 'SOURCE_EXPLICIT_REASON'),
    ('なら', 'SOURCE_EXPLICIT_CONDITION'),
    ('ならば', 'SOURCE_EXPLICIT_CONDITION'),
])
def test_existing_scope_operator_binds_the_evaluation_arguments_in_original_coordinates(marker, relation):
    text = ('  気持ちに余裕がない' + marker + '、\t私にとって必要かもしれないのは、'
            '🌱を眺めて過ごす時間です。\r\nまだ、自分でもよく分からない。  ')
    out = generated(text)
    meaning = out.source_meaning
    scope, = meaning.expression_scopes
    frame, = meaning.personal_evaluations
    assert scope.marker == marker and scope.relation == relation
    assert frame.commitment == 'POSSIBLE'
    assert frame.polarity == 'AFFIRMATIVE' and frame.temporal_scope == 'NONPAST'
    for a, b in (*zip(frame.scalar_parts, frame.utf8_parts, strict=True),
                 (scope.scope_scalar_span, scope.scope_utf8_span),
                 (scope.expression_scalar_span, scope.expression_utf8_span)):
        assert text[slice(*a)] == meaning.envelope.raw_utf8[slice(*b)].decode()
    assert text[slice(*frame.scalar_parts[0])] == '私'
    assert text[slice(*frame.scalar_parts[1])] == '必要かもしれない'
    assert text[slice(*frame.scalar_parts[2])] == '🌱を眺めて過ごす時間'
    assert all(scope.expression_scalar_span[0] <= a < b <= scope.expression_scalar_span[1]
               for a, b in frame.scalar_parts)
    assert out.artifact.piece_text == ('気持ちに余裕がない' + marker + '、私にとって、'
        '🌱を眺めて過ごす時間が必要かもしれない。まだ、自分でもよく分からない。')


@pytest.mark.parametrize('text', [
    '落ち着いて過ごせるなら、友人にとって大切なのは、一人で考える時間です。',
    '落ち着いて過ごせるなら、大切なのは、一人で考える時間です。',
    '落ち着いて過ごせるなら、私にとって大切なのは、一人で考える時間ではない。',
    '落ち着いて過ごせるなら、私にとって大切なのは、一人で考える時間だと友人が言った。',
    '落ち着いて過ごせるなら、私にとって大切なのは、その時間です。',
    '落ち着いて過ごせるなら、私にとって大切なのは、友人が好きなのは一人で過ごす時間です。',
    '落ち着いて過ごせるから、私にとって大切なのは、一人で過ごす時間です。',
    '落ち着いて過ごせるけれど、私にとって大切なのは、一人で過ごす時間です。',
    '私は気持ちを伝えたいので、私にとって大切なのは、一人で過ごす時間です。',
    '落ち着いて過ごせるなら、私が必要なのは、一人で過ごす時間です。',
    '落ち着いて過ごせるなら、私が好きなのは、東京大学教授です。',
    '落ち着いて過ごせるなら、私にとって大切なのは、佐藤さんと話す時間です。',
    '落ち着いて過ごせるなら、私にとって大切なのは、user@example.com に連絡することです。',
])
def test_unbound_viewpoints_targets_and_unmodelled_relations_are_not_invented(text):
    out = run(text, tier='premium')
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('fmt', ['quote', 'declaration'])
@pytest.mark.parametrize('marker', ['ので', 'なら'])
def test_scoped_evaluation_cannot_become_an_unconditional_standalone_value(fmt, marker):
    out = run('気持ちに余裕がない' + marker + '、私にとって大切なのは、家で静かに過ごす時間です。',
              tier='premium', requested_format=fmt)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('mutation', ['scope', 'evaluation', 'marker', 'argument', 'utf8', 'operation', 'blocks'])
def test_both_meanings_must_be_consumed_by_the_existing_plan_and_writer(mutation):
    out = generated(CASES[0][1]); m, p = out.source_meaning, out.artifact_plan
    if mutation == 'scope': m = replace(m, expression_scopes=())
    if mutation == 'evaluation': m = replace(m, personal_evaluations=())
    if mutation == 'marker': m = replace(m, expression_scopes=(replace(m.expression_scopes[0], marker='なら'),))
    if mutation == 'argument':
        f, = m.personal_evaluations
        m = replace(m, personal_evaluations=(replace(f, scalar_parts=(*f.scalar_parts[:2], (0, 1))),))
    if mutation == 'utf8':
        f, = m.personal_evaluations
        m = replace(m, personal_evaluations=(replace(f, utf8_parts=(*f.utf8_parts[:2], (0, 1))),))
    if mutation == 'operation':
        p = replace(p, duties=(replace(p.duties[0], operation='SOURCE_PERSONAL_EVALUATION'), *p.duties[1:]))
    if mutation == 'blocks': p = replace(p, block_node_ids=tuple((n.node_id,) for n in m.graph.nodes))
    with pytest.raises(ValueError):
        realize_piece_artifact(m, p, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_b9_uses_the_whole_scoped_canonical_body(ratio):
    class Metrics:
        profile_id = 'synthetic-scoped-evaluation-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    c = generated(CASES[0][1]).artifact.as_candidate()
    recipe = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(row['text'] for row in layout['lines']) == CASES[0][2]


def test_scoped_evaluation_target_and_later_reference_share_one_source_ordered_group():
    out = generated(CASES[5][1]); m = out.source_meaning
    ref, = m.nominal_references
    frame, = m.personal_evaluations
    assert ref.antecedent_scalar_span == frame.scalar_parts[2]
    assert ref.antecedent_utf8_span == frame.utf8_parts[2]
    assert ref.antecedent_node_id == m.expression_scopes[0].node_id
    assert out.artifact_plan.block_node_ids == (tuple(n.node_id for n in m.graph.nodes),)
