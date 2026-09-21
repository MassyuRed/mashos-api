"""Synthetic evaluation-target references composed with source-marked scopes."""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest, realize_piece_artifact
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


CASES = (
    ('linked_value_condition',
     '私にとって大切なのは、友人の佐藤さんと落ち着いて話す時間です。その時間が取れるなら、私は急がずに気持ちを伝えたい。まだ、会う日は決めていない。',
     '私にとって、友人と落ち着いて話す時間が大切です。私は、その時間が取れるなら、急がずに気持ちを伝えたい。まだ、会う日は決めていない。'),
    ('linked_preference_condition',
     '僕が好きなのは、小さく試して確かめることです。そのことを続けられるなら、僕は焦らずに学びたい。すぐに答えが出るとは限らない。',
     '僕は、小さく試して確かめることが好きです。僕は、そのことを続けられるなら、焦らずに学びたい。すぐに答えが出るとは限らない。'),
    ('linked_negative_value',
     '私にとって必要ではないのは、すぐに結論を出すことだ。そのことを相手にも求めたいわけではない。',
     '私にとって、すぐに結論を出すことが必要ではない。そのことを相手にも求めたいわけではない。'),
    ('linked_past_value',
     '私にとって大切だったのは、家族と毎日話す時間だ。この時間は昨日だけで、毎日あるわけではない。',
     '私にとって、家族と毎日話す時間が大切だった。この時間は昨日だけで、毎日あるわけではない。'),
    ('linked_tentative_reason',
     '私にとって必要かもしれないのは、一人で考えを整理する時間だ。その時間がまだ足りないので、私は答えを急ぎたくない。まだ、自分でもよく分からない。',
     '私にとって、一人で考えを整理する時間が必要かもしれない。私は、その時間がまだ足りないので、答えを急ぎたくない。まだ、自分でもよく分からない。'),
    ('linked_context_preference',
     '今週は予定が重なっていた。私が好きなのは、家で静かに過ごす時間です。この時間を確保できるかは、まだ分からない。',
     '今週は予定が重なっていた。\n\n私は、家で静かに過ごす時間が好きです。この時間を確保できるかは、まだ分からない。'),
    ('linked_distinct_targets',
     '私にとって大切なのは、家で静かに過ごす時間です。私が大切にしたいのは、自分で納得して選ぶことです。その時間が取れるなら、私は焦らずに考えたい。',
     '私にとって、家で静かに過ごす時間が大切です。私は、自分で納得して選ぶことを大切にしたい。私は、その時間が取れるなら、焦らずに考えたい。'),
    ('linked_object_reservation',
     '私が好きなのは、自分の手で長く使ってきたものです。このものには、使いながら直した跡が残っている。誰にでも勧めたいわけではない。',
     '私は、自分の手で長く使ってきたものが好きです。このものには、使いながら直した跡が残っている。誰にでも勧めたいわけではない。'),
)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-linked', PieceSourceSnapshot('synthetic-owner', 'synthetic-linked', 'v1', text),
        'synthetic-owner', 'synthetic-linked', 'v1', **kwargs))


def generated(text):
    out = run(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_evaluation_target_and_qualification_form_one_canonical_artifact(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert out.source_meaning.personal_evaluations and out.source_meaning.nominal_references
    assert any(d.operation == 'SOURCE_PERSONAL_EVALUATION' for d in out.artifact_plan.duties)
    if name in ('linked_value_condition', 'linked_preference_condition', 'linked_tentative_reason', 'linked_distinct_targets'):
        assert any(d.operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON' for d in out.artifact_plan.duties)
    for ref in out.source_meaning.nominal_references:
        assert any(ref.antecedent_node_id in block and ref.reference_node_id in block
                   for block in out.artifact_plan.block_node_ids)
    candidate = generate_piece_candidate(PieceSourceSnapshot('synthetic-owner', 'synthetic-linked', 'v1', text),
                                        authenticated_owner_id='synthetic-owner')
    assert candidate == out.artifact.as_candidate()
    assert not candidate['production_enabled'] and candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('text', [
    '私にとって大切なのは、家で過ごす時間です。私が望んでいるのは、友人と会う時間です。その時間が必要だ。',
    '私が望んでいるのは、家で過ごす時間です。私にとって大切なのは、友人と会う時間です。その時間が必要だ。',
    '私にとって大切なのは、家で過ごす時間です。職場でも休む時間があった。その時間が必要だ。',
    '私にとって大切なのは、家で過ごす時間です。そのことを続けたい。',
    '私にとって大切なのは、家で過ごす時間です。その時間帯は混雑する。',
    '私にとって大切なのは、ひとりの機会より、家で過ごす時間です。その時間が必要だ。',
    '私にとって大切なのは、家で過ごす時間です。それが必要だ。',
    'その時間は昨日取れなかった。私にとって大切なのは、家で過ごす時間です。',
])
def test_competing_missing_composite_and_unbound_references_remain_unavailable(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_actual_evaluative_argument_ranges_bind_before_name_publicization():
    text = '  私にとって大切なのは、🌱を眺めて静かに過ごす時間です。\r\nその時間が取れるなら、私は慌てずに一日を始めたい。  '
    out = generated(text)
    meaning = out.source_meaning
    frame, = meaning.personal_evaluations
    ref, = meaning.nominal_references
    scope, = meaning.expression_scopes
    assert ref.antecedent_scalar_span == frame.scalar_parts[2]
    assert ref.antecedent_utf8_span == frame.utf8_parts[2]
    assert scope.node_id == ref.reference_node_id
    for scalar, utf8 in [(ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                         (ref.reference_scalar_span, ref.reference_utf8_span),
                         (scope.scope_scalar_span, scope.scope_utf8_span)]:
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    assert text[slice(*ref.antecedent_scalar_span)] == '🌱を眺めて静かに過ごす時間'
    assert out.artifact.piece_text == '私にとって、🌱を眺めて静かに過ごす時間が大切です。私は、その時間が取れるなら、慌てずに一日を始めたい。'


@pytest.mark.parametrize('mutation', ['evaluation', 'reference', 'scope', 'edge', 'split', 'reverse'])
def test_all_three_semantic_duties_are_consumed_by_the_same_author(mutation):
    out = generated(CASES[0][1]); meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'evaluation': meaning = replace(meaning, personal_evaluations=())
    if mutation == 'reference': meaning = replace(meaning, nominal_references=())
    if mutation == 'scope': meaning = replace(meaning, expression_scopes=())
    if mutation == 'edge': meaning = replace(meaning, graph=replace(meaning.graph, edges=tuple(
        e for e in meaning.graph.edges if e.relation != 'SOURCE_BOUND_NOMINAL_REFERENCE')))
    if mutation == 'split': plan = replace(plan, block_node_ids=tuple((n.node_id,) for n in meaning.graph.nodes))
    if mutation == 'reverse': plan = replace(plan, block_node_ids=(tuple(n.node_id for n in reversed(meaning.graph.nodes)),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('fmt', ['quote', 'declaration'])
def test_condition_cannot_lose_its_value_antecedent_for_a_standalone_format(fmt):
    out = run(CASES[0][1], tier='premium', requested_format=fmt)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_linked_actual_body_is_the_only_b9_layout_body(ratio):
    class Metrics:
        profile_id = 'synthetic-linked-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    candidate = generated(CASES[0][1]).artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(row['text'] for row in layout['lines']) == CASES[0][2]


def test_reference_chain_keeps_past_negation_and_duplicate_reservations():
    text = '私にとって大切なのは、家で過ごす時間です。その時間は、昨日は取れなかった。私はその時間を毎日少しでも持ちたい。まだ予定は決めていない。まだ予定は決めていない。'
    out = generated(text)
    assert len(out.source_meaning.nominal_references) == 2
    assert out.artifact.piece_text == '私にとって、家で過ごす時間が大切です。その時間は、昨日は取れなかった。私は、その時間を毎日少しでも持ちたい。まだ予定は決めていない。まだ予定は決めていない。'
