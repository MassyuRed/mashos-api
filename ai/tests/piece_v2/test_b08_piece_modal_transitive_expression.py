"""A written outer modal is not an asserted wish, refusal or present pledge.

Synthetic sources only. Exercise the same disabled source/plan/author/B9 path,
without changing old tests, policy limits, dependencies or activation. Literal
finite forms below are independent of the production inflection derivation.
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

TARGET = '窓辺で静かに草花を眺めて過ごす時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
MODALS = ('かもしれない', 'かもしれません', 'とは限らない', 'とは限りません')
FORMS = (
    ('大切にしたい', False), ('大切にしている', False),
    ('大切にしたくない', False), ('望んでいる', False),
    ('望んでいない', False), ('選びたい', False), ('選びたくない', False),
    ('大切にしたかった', True), ('大切にしていた', True),
    ('大切にしたくなかった', True), ('望んでいた', True),
    ('望んでいなかった', True), ('選びたかった', True), ('選びたくなかった', True),
)


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'modal-transitive', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'modal-transitive', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_artifact(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for group in plan.block_node_ids for n in group) == tuple(
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
    assert realize_piece_artifact(meaning, plan, tier=tier,
        requested_format=requested_format) == out.artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    source = PieceSourceSnapshot('synthetic-owner', 'modal-transitive', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert not plan.declaration_eligible
    assert 'declaration' not in candidate['eligible_formats']
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    return out


@pytest.mark.parametrize('predicate,past', FORMS)
@pytest.mark.parametrize('modal', MODALS)
def test_the_whole_written_modal_predicate_keeps_its_time_and_negation(predicate, past, modal):
    text = '私は' + TARGET + 'を' + predicate + modal + '。'
    out = assert_artifact(text, '私は、' + TARGET + 'を' + predicate + modal + '。')
    direct = _direct_transitive_expression(text)
    assert direct['predicate'] == predicate + modal
    assert direct['modal'] == modal
    assert direct['past_predicate'] == (predicate if past else None)
    assert out.artifact_plan.duties[0].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'
    assert out.artifact.eligible_formats == ('short_essay', 'quote')
    refused = outcome(text, tier='premium', requested_format='declaration')
    assert refused.status == EngineStatus.UNAVAILABLE
    assert refused.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_a_tentative_antecedent_keeps_its_own_predicate_and_the_next_preference(speaker):
    first = speaker + 'は' + TARGET + 'を望んでいなかったかもしれません。'
    second = 'その時間が好きとは限りません。'
    out = assert_artifact(first + speaker + 'は' + second + TAIL,
        speaker + 'は、' + TARGET + 'を望んでいなかったかもしれません。' + second + TAIL)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert first[slice(*ref.antecedent_scalar_span)] == TARGET
    frame, = out.source_meaning.personal_evaluations
    assert (frame.temporal_scope, frame.polarity, frame.commitment) == (
        'NONPAST', 'AFFIRMATIVE', 'NON_UNIVERSAL')


@pytest.mark.parametrize('premise,relation', (
    ('予定を空けられるなら', 'SOURCE_EXPLICIT_CONDITION'),
    ('余裕がなかったので', 'SOURCE_EXPLICIT_REASON'),
    ('まだ迷っていたけれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('以前は', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
    ('当時も', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
    ('今は', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
    ('現在も', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
))
def test_outer_clause_scope_and_inner_modal_stay_separate(premise, relation):
    first = premise + '、私は' + TARGET + 'を大切にしたくなかったかもしれません。'
    second = '私はその時間が好きでした。'
    out = assert_artifact(first + second + TAIL, first + '私は、その時間が好きでした。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == relation
    assert first[slice(*scope.scope_scalar_span)] == premise
    assert first[slice(*scope.expression_scalar_span)].endswith('大切にしたくなかったかもしれません。')


@pytest.mark.parametrize('modal', MODALS)
def test_prior_context_is_not_fronted_over_a_tentative_present_expression(modal):
    context = '学生のころは予定が少なかった。'
    text = context + '私は' + TARGET + 'を望んでいる' + modal + '。'
    out = assert_artifact(text, context + '私は、' + TARGET + 'を望んでいる' + modal + '。')
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2'),)


def test_public_role_unicode_and_source_newline_keep_the_complete_tentative_body():
    target = '私の友人の秋山さんと🌱を静かに眺める時間'
    first = '私は' + target + 'を望んでいたとは限りません。'
    text = '\t' + first + '\r\n　私はその時間が苦手ではないかもしれません。' + TAIL
    out = assert_artifact(text,
        '私は、私の友人と🌱を静かに眺める時間を望んでいたとは限りません。'
        '私は、その時間が苦手ではないかもしれません。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target


def test_same_author_condition_keeps_its_first_topic_and_modal_rejection():
    text = '僕は迷っているけれど、僕は' + TARGET + 'を選びたくないかもしれません。' + TAIL
    assert_artifact(text, '僕は迷っているけれど、' + TARGET + 'を選びたくないかもしれません。' + TAIL)


def test_reference_to_a_prior_value_does_not_inherit_its_certainty():
    first = '私にとって' + TARGET + 'が大切です。'
    second = '私はその時間を望んでいるとは限りません。'
    out = assert_artifact(first + second,
        '私にとって、' + TARGET + 'が大切です。私は、その時間を望んでいるとは限りません。')
    assert out.source_meaning.nominal_references[0].antecedent_node_id == 'piece:s1'


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_format_selection_never_makes_a_polite_nonuniversal_statement_a_pledge(tier):
    text = '私は' + TARGET + 'を望んでいるとは限りません。'
    out = assert_artifact(text, '私は、' + TARGET + 'を望んでいるとは限りません。', tier=tier)
    assert out.artifact.format_type == ('short_essay' if tier == 'free' else 'quote')
    for fmt in ('short_essay', 'quote'):
        chosen = outcome(text, tier=tier, requested_format=fmt)
        assert chosen.status == (EngineStatus.GENERATED if tier == 'premium' else EngineStatus.UNAVAILABLE)


@pytest.mark.parametrize('text', (
    '彼は' + TARGET + 'を望んでいるかもしれない。',
    TARGET + 'を望んでいるかもしれない。',
    '私はその時間を望んでいるかもしれない。',
    '私は' + TARGET + 'を望んでいますかもしれない。',
    '私は' + TARGET + 'を望んでいませんかもしれない。',
    '私は' + TARGET + 'を望んでいましたかもしれない。',
    '私は' + TARGET + 'を望んでいませんでしたとは限りません。',
    '私は' + TARGET + 'を選びたいですかもしれません。',
    '私は' + TARGET + 'を選びたかったですとは限らない。',
    '私は' + TARGET + 'を望んでいるかもしれないとは限らない。',
    '私は' + TARGET + 'を望んでいるかもしれませんと聞いた。',
    '私は' + TARGET + 'を望んでいるかもしれないと思う。',
    '私は' + TARGET + 'を選ぶかもしれません。',
    '私が望んでいるかもしれないのは' + TARGET + 'です。',
))
def test_modal_does_not_supply_a_missing_author_referent_verb_or_embedded_grammar(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('change', ('declaration', 'predicate', 'duty'))
def test_a_forged_plan_or_missing_modal_cannot_produce_an_assertion(change):
    text = '私は' + TARGET + 'を望んでいるとは限りません。'
    out = assert_artifact(text, '私は、' + TARGET + 'を望んでいるとは限りません。')
    meaning, plan = out.source_meaning, out.artifact_plan
    if change == 'declaration':
        plan = replace(plan, declaration_eligible=True)
    elif change == 'predicate':
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(replace(
            meaning.graph.nodes[0], value='私は' + TARGET + 'を望んでいる。'),)))
    else:
        plan = replace(plan, duties=(replace(plan.duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT'),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='premium', requested_format=None)


class Metrics:
    profile_id = 'modal-transitive-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, size):
        width = len(text) * size
        return TextMeasurement(width, 0, -.8 * size, width, .2 * size)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_the_same_tentative_text_reaches_the_unchanged_layout(ratio):
    text = '私は' + TARGET + 'を大切にしたいかもしれません。' + TAIL
    out = assert_artifact(text, '私は、' + TARGET + 'を大切にしたいかもしれません。' + TAIL)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
        for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
