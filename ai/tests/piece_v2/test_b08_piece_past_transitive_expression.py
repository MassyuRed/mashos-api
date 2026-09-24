"""Source-written past expressions remain past, not a present declaration.

Synthetic sources exercise the existing disabled B8/CMEE/B9 path. No lexical
predicate, public route, policy threshold, original test or external dependency
is supplied by these tests. The finite past/register expectations are literal
and independent of the production inflection builder.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import _direct_transitive_expression
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TARGET = '一人で静かに手帳を開いて読み返す時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
PAST = (
    '大切にしたかった', '大切にしたかったです',
    '大切にしていた', '大切にしていました',
    '大切にしたくなかった', '大切にしたくなかったです',
    '望んでいた', '望んでいました',
    '望んでいなかった', '望んでいませんでした',
    '選びたかった', '選びたかったです',
    '選びたくなかった', '選びたくなかったです',
)


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'past-expression', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'past-expression', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_artifact(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for block in plan.block_node_ids for n in block) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                            (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                            (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    frozen = asdict(meaning), asdict(plan)
    assert realize_piece_artifact(meaning, plan, tier=tier, requested_format=requested_format) == out.artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    source = PieceSourceSnapshot('synthetic-owner', 'past-expression', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    assert not plan.declaration_eligible
    assert 'declaration' not in candidate['eligible_formats']
    return out


@pytest.mark.parametrize('predicate', PAST)
@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_past_expression_is_preserved_without_becoming_a_current_declaration(predicate, tier):
    text = '私は' + TARGET + 'を' + predicate + '。'
    out = assert_artifact(text, '私は、' + TARGET + 'を' + predicate + '。', tier=tier)
    direct = _direct_transitive_expression(text)
    assert direct['predicate'] == direct['past_predicate'] == predicate
    assert out.artifact_plan.duties[0].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'
    assert out.artifact.eligible_formats == ('short_essay', 'quote')
    assert out.artifact.format_type == ('short_essay' if tier == 'free' else 'quote')
    refused = outcome(text, tier='premium', requested_format='declaration')
    assert refused.status == EngineStatus.UNAVAILABLE
    assert refused.reason_codes == ('format_choice_not_admitted',)
    assert refused.artifact is None


@pytest.mark.parametrize('predicate', PAST)
def test_past_antecedent_binds_the_whole_reference_and_preserves_later_reservation(predicate):
    first = '私は' + TARGET + 'を' + predicate + '。'
    second = 'その時間が好きではなかったかもしれません。'
    out = assert_artifact(first + '私は' + second + TAIL,
        '私は、' + TARGET + 'を' + predicate + '。' + second + TAIL)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert out.source_meaning.envelope.raw_utf8[slice(*ref.antecedent_utf8_span)] == TARGET.encode()
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')
    assert out.artifact.eligible_formats == ('short_essay',)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_literal_speaker_is_retained_without_a_past_to_present_conversion(speaker):
    text = speaker + 'は' + TARGET + 'を望んでいませんでした。'
    assert_artifact(text, speaker + 'は、' + TARGET + 'を望んでいませんでした。')


@pytest.mark.parametrize('premise,relation', (
    ('予定を空けられるなら', 'SOURCE_EXPLICIT_CONDITION'),
    ('余裕がなかったので', 'SOURCE_EXPLICIT_REASON'),
    ('まだ迷っていたけれど', 'SOURCE_EXPLICIT_CONCESSION'),
))
def test_written_scope_does_not_become_an_unconditional_past_or_present_intention(premise, relation):
    first = premise + '、私は' + TARGET + 'を大切にしたかったです。'
    text = first + '私はその時間が好きでした。' + TAIL
    out = assert_artifact(text, first + '私は、その時間が好きでした。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == relation
    assert out.source_meaning.envelope.raw_utf8[slice(*scope.scope_utf8_span)] == premise.encode()


def test_same_author_scope_keeps_its_first_author_and_complete_past_predicate():
    first = '僕は迷っていたけれど、僕は' + TARGET + 'を選びたくなかったです。'
    out = assert_artifact(first + TAIL,
        '僕は迷っていたけれど、' + TARGET + 'を選びたくなかったです。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == 'SOURCE_EXPLICIT_CONCESSION'


@pytest.mark.parametrize('target,head', (
    ('自分の言葉で日々を記すこと', 'こと'),
    ('長く自分の手元に置いてきたもの', 'もの'),
    ('🌱を窓辺で静かに眺める時間', '時間'),
))
def test_past_object_is_not_truncated_or_given_the_evaluations_tense(target, head):
    first = '僕は' + target + 'を大切にしていた。'
    second = 'この' + head + 'が苦手とは限りません。'
    assert_artifact(first + '僕は' + second + TAIL,
        '僕は、' + target + 'を大切にしていた。' + second + TAIL)


def test_past_public_role_and_original_unicode_coordinates_are_kept():
    target = '私の友人の秋山さんと落ち着いて話す時間'
    text = '🌱を見た。\r\n\u3000私は' + target + 'を大切にしていました。\t私はその時間が好きでした。' + TAIL
    out = assert_artifact(text,
        '🌱を見た。\n\n私は、私の友人と落ち着いて話す時間を大切にしていました。その時間が好きでした。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert text.encode()[slice(*ref.antecedent_utf8_span)] == target.encode()
    assert '秋山' not in out.artifact.piece_text


def test_a_past_reference_is_not_a_new_antecedent_or_a_change_in_current_value():
    first = '私にとって' + TARGET + 'が大切です。'
    second = '私はその時間を望んでいませんでした。'
    out = assert_artifact(first + second + TAIL,
        '私にとって、' + TARGET + 'が大切です。私は、その時間を望んでいませんでした。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == 'piece:s1'


def test_past_and_explicit_current_evaluation_are_not_replaced_by_a_guessed_transition():
    first = '私は' + TARGET + 'を大切にしていました。'
    second = '今は、私はその時間が苦手かもしれません。'
    out = assert_artifact(first + second + TAIL, '私は、' + TARGET + 'を大切にしていました。' + second + TAIL)
    assert {e.relation for e in out.source_meaning.graph.edges} == {'SOURCE_ORDER', 'SOURCE_BOUND_NOMINAL_REFERENCE'}


@pytest.mark.parametrize('operator', ('と', 'より'))
def test_paired_past_and_nonpast_expressions_keep_both_predicates_and_comparison_direction(operator):
    other = '自分の言葉で日々を記すこと'
    first = '私は' + TARGET + 'を大切にしていました。'
    second = '私は' + other + 'を望んでいません。'
    third = 'その時間' + operator + '、このことが好きではないかもしれません。'
    out = assert_artifact(first + second + '私は' + third + TAIL,
        '私は、' + TARGET + 'を大切にしていました。' + other + 'を望んでいません。' + third + TAIL)
    assert [r.antecedent_node_id for r in out.source_meaning.nominal_references] == ['piece:s1', 'piece:s2']


@pytest.mark.parametrize('gap', ('\n', '\r\n'))
def test_source_line_boundary_does_not_erase_a_following_author(gap):
    text = '私は' + TARGET + 'を大切にしていました。' + gap + '私はその時間が好きでした。' + TAIL
    assert_artifact(text, '私は、' + TARGET + 'を大切にしていました。私は、その時間が好きでした。' + TAIL)


@pytest.mark.parametrize('sentence', (
    '彼は一人で静かに手帳を開く時間を望んでいた。',
    '一人で静かに手帳を開く時間を望んでいた。',
    '私は一人で静かに手帳を開く時間を望んでいたかもしれない。',
    '私は一人で静かに手帳を開く時間を望んでいましたと聞いた。',
    '私は一人で静かに手帳を開く時間を大切にしたいでした。',
    '私は一人で静かに手帳を開く時間を選びました。',
    '私は一人で静かに手帳を開く時間を望んでいましたか？',
    '私はその時間を望んでいました。',
))
def test_past_inflection_does_not_infer_author_reference_other_verb_or_modal(sentence):
    out = outcome(sentence)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('mutation', ('declaration', 'predicate', 'duty'))
def test_past_admission_cannot_be_forged_into_a_current_declaration_or_another_body(mutation):
    text = '私は' + TARGET + 'を大切にしていました。'
    out = assert_artifact(text, '私は、' + TARGET + 'を大切にしていました。')
    meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'declaration':
        plan = replace(plan, declaration_eligible=True)
    elif mutation == 'predicate':
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(replace(
            meaning.graph.nodes[0], value='私は' + TARGET + 'を大切にしています。'),)))
    else:
        plan = replace(plan, duties=(replace(plan.duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT'),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='premium', requested_format=None)


class Metrics:
    profile_id = 'past-expression-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, size):
        width = len(text) * size
        return TextMeasurement(width, 0, -.8 * size, width, .2 * size)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_the_past_body_is_the_exact_existing_layout_input(ratio):
    text = '私は' + TARGET + 'を大切にしていました。私はその時間が好きでした。' + TAIL
    out = assert_artifact(text, '私は、' + TARGET + 'を大切にしていました。その時間が好きでした。' + TAIL)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(r['text'] for r in layout['lines'] if r['block_index'] == i)
        for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']


def test_short_past_source_keeps_the_existing_minimum_envelope():
    text = '私は一人で静かに手帳を開く時間を望んでいた。'
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_not_eligible',)
    out = assert_artifact(text, '私は、一人で静かに手帳を開く時間を望んでいた。', tier='plus')
    assert out.artifact.eligible_formats == ('quote',)
    assert out.artifact.format_type == 'quote'
    out = outcome(text, tier='premium', requested_format='short_essay')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('context', (
    '学生のころは時間に余裕があった。',
    '雨の日には手帳を開いていた。',
))
def test_prior_context_stays_before_the_past_expression_not_after_a_fronted_wish(context):
    text = context + '私は' + TARGET + 'を大切にしていました。'
    out = assert_artifact(text, context + '私は、' + TARGET + 'を大切にしていました。')
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2'),)
    assert out.artifact.eligible_formats == ('short_essay',)
