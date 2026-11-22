"""Written time topics scope the existing direct personal-expression grammar.

Synthetic sources only. Time, negation, author and the whole object are kept;
a former value and a current refusal never become an inferred transition or
present pledge. Existing policy, old tests and production activation stay put.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TARGET = '一人で静かに手帳を開いて読み返す時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
TIMES = ('以前は', '以前も', '当時は', '当時も', '今は', '今も', '現在は', '現在も')


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'temporal-transitive', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'temporal-transitive', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_artifact(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for group in plan.block_node_ids for n in group) == tuple(
        node.node_id for node in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    for scope in meaning.expression_scopes:
        assert scope.relation == 'SOURCE_EXPLICIT_TIME_CONTEXT'
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                            (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                            (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    frozen = asdict(meaning), asdict(plan)
    assert realize_piece_artifact(meaning, plan, tier=tier,
        requested_format=requested_format) == out.artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    source = PieceSourceSnapshot('synthetic-owner', 'temporal-transitive', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not plan.declaration_eligible
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    return out


@pytest.mark.parametrize('time_topic', TIMES)
@pytest.mark.parametrize('predicate', (
    '大切にしています', '大切にしていました',
    '望んでいません', '望んでいませんでした',
    '選びたくないです', '選びたくなかったです',
))
def test_time_and_its_particle_never_overwrite_the_written_predicate(time_topic, predicate):
    text = time_topic + '、私は' + TARGET + 'を' + predicate + '。'
    out = assert_artifact(text, text)
    scope, = out.source_meaning.expression_scopes
    assert text[slice(*scope.scope_scalar_span)] == time_topic
    assert scope.marker == time_topic[-1]
    assert text[slice(*scope.expression_scalar_span)] == '私は' + TARGET + 'を' + predicate + '。'
    assert out.source_meaning.graph.nodes[0].node_kind == 'PIECE_SOURCE_TIME_SCOPED_EXPRESSION'
    assert out.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert not out.source_meaning.personal_evaluations


@pytest.mark.parametrize('predicate', (
    '大切にしたかった', '大切にしたかったです',
    '大切にしていた', '大切にしていました',
    '大切にしたくなかった', '大切にしたくなかったです',
    '望んでいた', '望んでいました',
    '望んでいなかった', '望んでいませんでした',
    '選びたかった', '選びたかったです',
    '選びたくなかった', '選びたくなかったです',
))
def test_existing_past_register_forms_keep_their_complete_time_context(predicate):
    text = '以前は、私は' + TARGET + 'を' + predicate + '。' + TAIL
    assert_artifact(text, text)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_past_value_and_current_refusal_keep_one_target_but_separate_expressions(speaker):
    text = ('以前は、' + speaker + 'は' + TARGET + 'を大切にしていました。'
            '今は、' + speaker + 'はその時間を望んでいません。' + TAIL)
    out = assert_artifact(text, text)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert text[slice(*ref.antecedent_scalar_span)] == TARGET
    assert text[slice(*ref.reference_scalar_span)] == 'その時間'
    assert [text[slice(*s.scope_scalar_span)] for s in out.source_meaning.expression_scopes] == ['以前は', '今は']
    assert {e.relation for e in out.source_meaning.graph.edges} == {'SOURCE_ORDER', 'SOURCE_BOUND_NOMINAL_REFERENCE'}


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_a_time_qualified_expression_cannot_be_excerpted_as_quote_or_declaration(tier):
    text = '今は、私は' + TARGET + 'を大切にしたい。'
    assert_artifact(text, text, tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text, tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE
        assert out.reason_codes == ('format_choice_not_admitted',)
        assert out.artifact is None
    if tier == 'premium':
        assert_artifact(text, text, tier=tier, requested_format='short_essay')


@pytest.mark.parametrize('separator', ('、', '，', ',', '、\t', '、　'))
def test_original_coordinates_include_emoji_and_do_not_rebase_across_separators(separator):
    target = '🌱を窓辺で静かに眺めて過ごす時間'
    text = '\n\t以前は' + separator + '僕は' + target + 'を大切にしていました。\r\n　今は、僕はこの時間を望んでいません。' + TAIL
    expected = '以前は、僕は' + target + 'を大切にしていました。今は、僕はこの時間を望んでいません。' + TAIL
    out = assert_artifact(text, expected)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target


def test_a_following_preference_keeps_its_own_author_and_uncertainty_after_time_scope():
    first = '以前は、私は' + TARGET + 'を大切にしていました。'
    second = '私はその時間が好きではなかったかもしれません。'
    out = assert_artifact(first + second + TAIL,
        first + '私は、その時間が好きではなかったかもしれません。' + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')


def test_existing_evaluation_can_introduce_a_time_scoped_direct_reference():
    first = '私にとって' + TARGET + 'が大切です。'
    second = '当時は、私はその時間を望んでいませんでした。'
    out = assert_artifact(first + second + TAIL,
        '私にとって、' + TARGET + 'が大切です。' + second + TAIL)
    ref, = out.source_meaning.nominal_references
    frame, = out.source_meaning.personal_evaluations
    assert ref.antecedent_scalar_span == frame.scalar_parts[2]


def test_written_public_role_and_the_entire_temporal_expression_are_kept():
    target = '私の友人の秋山さんと落ち着いて言葉を交わす時間'
    text = '当時も、私は' + target + 'を大切にしていました。今は、私はその時間を望んでいません。' + TAIL
    expected = '当時も、私は私の友人と落ち着いて言葉を交わす時間を大切にしていました。今は、私はその時間を望んでいません。' + TAIL
    out = assert_artifact(text, expected)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target


def test_prior_context_is_not_moved_behind_a_time_qualified_wish():
    text = '学生のころは予定が少なかった。当時は、私は' + TARGET + 'を大切にしたかった。' + TAIL
    out = assert_artifact(text, text)
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3'),)


@pytest.mark.parametrize('text', (
    '以前は、彼は' + TARGET + 'を望んでいた。',
    '以前は、' + TARGET + 'を望んでいた。',
    '以前は私は' + TARGET + 'を望んでいた。',
    '今後は、私は' + TARGET + 'を大切にしたい。',
    '以前は、今は、私は' + TARGET + 'を望んでいた。',
    '以前は、私はその時間を望んでいた。',
    '以前は、私は' + TARGET + 'を望んでいたかもしれない。',
    '以前は、私は' + TARGET + 'を望んでいましたと聞いた。',
    '以前は、私は' + TARGET + 'を選びました。',
    '以前は、私は' + TARGET + 'を大切にしたいでした。',
    '今は、私が大切にしたいのは' + TARGET + 'です。',
    '今は、私は一人で静かに手帳を開きたい。',
    '私は以前は、私は' + TARGET + 'を大切にしていた。',
    '予定を空けられるなら、今は、私は' + TARGET + 'を大切にしている。',
))
def test_time_alone_does_not_supply_an_author_reference_predicate_or_nested_scope(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


def test_competing_time_scoped_objects_are_not_resolved_by_recency():
    text = ('以前は、私は窓辺で静かに草花を眺める時間を大切にしていた。'
            '今は、私は机で静かに手帳を読み返す時間を大切にしている。'
            '今は、私はその時間が好きです。' + TAIL)
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('evaluation_target_not_self_contained',)


@pytest.mark.parametrize('change', ('relation', 'marker', 'span', 'removed', 'declaration'))
def test_a_forged_scope_or_plan_cannot_change_time_or_create_a_pledge(change):
    text = '以前は、私は' + TARGET + 'を望んでいませんでした。'
    out = assert_artifact(text, text)
    meaning, plan = out.source_meaning, out.artifact_plan
    scope, = meaning.expression_scopes
    if change == 'declaration':
        plan = replace(plan, declaration_eligible=True)
    else:
        altered = (() if change == 'removed' else (replace(scope, **{
            'relation': {'relation': 'SOURCE_EXPLICIT_REASON'},
            'marker': {'marker': 'も'},
            'span': {'scope_scalar_span': (1, scope.scope_scalar_span[1])},
        }[change]),))
        meaning = replace(meaning, expression_scopes=altered)
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


class Metrics:
    profile_id = 'temporal-transitive-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, size):
        width = len(text) * size
        return TextMeasurement(width, 0, -.8 * size, width, .2 * size)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_past_and_current_clauses_both_reach_the_unchanged_layout(ratio):
    text = '以前は、私は' + TARGET + 'を大切にしていました。今は、私はその時間を望んでいません。' + TAIL
    out = assert_artifact(text, text)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
        for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']


def test_short_temporal_source_does_not_bypass_the_existing_envelope():
    out = outcome('今は、私は本を読むことを望んでいる。', tier='premium')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_not_eligible',)
    assert out.artifact is None
