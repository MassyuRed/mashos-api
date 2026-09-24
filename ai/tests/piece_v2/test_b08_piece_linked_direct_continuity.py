"""A direct antecedent and its scoped wish can share one explicit author.

Synthetic inputs only. This optional realization edit does not admit a new
source, infer a subject, alter a graph/plan or claim native/product acceptance.
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

TARGET = '窓辺で静かに草花を眺めて過ごす時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
WISH = '考えをゆっくり整理したいです。'
PREDICATES = (
    '大切にしたい', '大切にしたいです', '大切にしています',
    '選びたくない', '望んでいました', '選びたかったです',
    '大切にしたいかもしれません', '望んでいたかもしれない',
    '望んでいなかったとは限りません',
)
PREMISES = ('その時間が取れるなら', 'その時間が取れたので', 'その時間が短かったけれど')


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'linked-direct', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'linked-direct', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
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
    assert realize_piece_artifact(meaning, plan, tier=tier,
        requested_format=requested_format) == out.artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    source = PieceSourceSnapshot('synthetic-owner', 'linked-direct', 'v1', text)
    c = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
                                tier=tier, requested_format=requested_format)
    assert c == out.artifact.as_candidate()
    assert c['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert c['eligible_formats'] == ['short_essay']
    assert not plan.declaration_eligible
    assert c['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert c['production_enabled'] is False
    assert c['record_effect'] == c['quota_effect'] == 0
    assert not out.automatic_progression
    return out


@pytest.mark.parametrize('predicate', PREDICATES)
@pytest.mark.parametrize('premise', PREMISES)
def test_scoped_wish_shares_only_the_direct_antecedents_author(predicate, premise):
    first = '私は' + TARGET + 'を' + predicate + '。'
    text = first + premise + '、私は' + WISH + TAIL
    out = assert_body(text, '私は、' + TARGET + 'を' + predicate + '。' + premise + '、' + WISH + TAIL)
    ref, = out.source_meaning.nominal_references
    scope, = out.source_meaning.expression_scopes
    assert ref.antecedent_node_id == 'piece:s1' and ref.reference_node_id == 'piece:s2'
    assert text[slice(*ref.antecedent_scalar_span)] == TARGET
    assert text[slice(*scope.scope_scalar_span)] == premise
    assert text[slice(*scope.expression_scalar_span)] == '私は' + WISH
    assert out.artifact_plan.duties[1].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_author_spelling_determiner_and_negative_wish_are_not_normalized(speaker, determiner):
    first = speaker + 'は' + TARGET + 'を望んでいなかったかもしれません。'
    premise = determiner + '時間が取れるならば'
    wish = '答えを急ぎたくないです。'
    assert_body(first + premise + '、' + speaker + 'は' + wish + TAIL,
        speaker + 'は、' + TARGET + 'を望んでいなかったかもしれません。' + premise + '、' + wish + TAIL)


@pytest.mark.parametrize('gap', ('\n', '\r\n', '\r', '\n\n'))
def test_source_line_breaks_decline_only_the_optional_omission(gap):
    first = '私は' + TARGET + 'を大切にしています。'
    assert_body(first + gap + PREMISES[0] + '、私は' + WISH + TAIL,
        '私は、' + TARGET + 'を大切にしています。' + PREMISES[0] + '、私は、' + WISH + TAIL)


@pytest.mark.parametrize('speaker', ('僕', 'わたし'))
def test_a_different_written_speaker_is_not_an_alias(speaker):
    assert_body('私は' + TARGET + 'を大切にしています。' + PREMISES[0] + '、' + speaker + 'は' + WISH + TAIL,
        '私は、' + TARGET + 'を大切にしています。' + PREMISES[0] + '、' + speaker + 'は、' + WISH + TAIL)


@pytest.mark.parametrize('middle', ('今日は空が明るかった。', '友人は別の予定を立てていた。'))
def test_intervening_context_cannot_be_crossed(middle):
    assert_body('私は' + TARGET + 'を大切にしています。' + middle + PREMISES[0] + '、私は' + WISH + TAIL,
        '私は、' + TARGET + 'を大切にしています。' + middle + PREMISES[0] + '、私は、' + WISH + TAIL)


@pytest.mark.parametrize('premise', (
    'その時間は友人が用意したので', 'その時間を今も迷っているので',
    'その時間は短いけれども',
))
def test_later_scope_subject_or_contrast_retains_the_topic(premise):
    # The connective's own も is not a contrast. The short concession remains editable.
    retained = '' if premise == 'その時間は短いけれども' else '私は、'
    assert_body('私は' + TARGET + 'を大切にしています。' + premise + '、私は' + WISH + TAIL,
        '私は、' + TARGET + 'を大切にしています。' + premise + '、' + retained + WISH + TAIL)


@pytest.mark.parametrize('target', ('友人が静かに過ごす時間', '友人も静かに過ごす時間'))
def test_a_participant_inside_the_antecedent_does_not_become_the_wish_author(target):
    assert_body('私は' + target + 'を望んでいます。' + PREMISES[0] + '、私は' + WISH + TAIL,
        '私は、' + target + 'を望んでいます。' + PREMISES[0] + '、私は、' + WISH + TAIL)


def test_a_competing_topic_inside_the_following_wish_keeps_the_explicit_author():
    wish = '休憩は静かに過ごしたいです。'
    assert_body('私は' + TARGET + 'を望んでいます。' + PREMISES[0] + '、私は' + wish + TAIL,
        '私は、' + TARGET + 'を望んでいます。' + PREMISES[0] + '、私は、' + wish + TAIL)


def test_scoped_antecedent_and_evaluative_viewpoint_stay_outside_this_edit():
    first = '以前は、私は' + TARGET + 'を望んでいました。'
    assert_body(first + PREMISES[0] + '、私は' + WISH + TAIL,
                first + PREMISES[0] + '、私は、' + WISH + TAIL)
    first = '私は' + TARGET + 'を望んでいます。'
    second = PREMISES[0] + '、私にとって答えを急がないことが大切です。'
    assert_body(first + second + TAIL,
        '私は、' + TARGET + 'を望んでいます。' + PREMISES[0] + '、私にとって、答えを急がないことが大切です。' + TAIL)


def test_scoped_direct_predicate_keeps_its_separate_realization():
    second = PREMISES[0] + '、私は机で紙を折ることを選びたい。'
    assert_body('私は' + TARGET + 'を望んでいます。' + second + TAIL,
        '私は、' + TARGET + 'を望んでいます。' + second + TAIL)


def test_role_publicization_and_unicode_keep_original_coordinates():
    target = '私の友人の秋山さんと🌱を静かに眺める時間'
    text = '\t私は' + target + 'を望んでいました。\t　' + PREMISES[0] + '、私は' + WISH + TAIL
    out = assert_body(text, '私は、私の友人と🌱を静かに眺める時間を望んでいました。' + PREMISES[0] + '、' + WISH + TAIL)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target


def test_an_optional_edit_cannot_make_an_admitted_short_essay_too_short():
    # Deliberately minimal synthetic grammar, not a proposed product example.
    text = '私はものを選びたい。そのものとなら、私は寝たい。'
    expected = '私は、ものを選びたい。そのものとなら、私は、寝たい。'
    assert len(expected) == 26 and len(expected.replace('、私は、', '、')) == 23
    assert_body(text, expected)


@pytest.mark.parametrize('text', (
    'その時間が取れるなら、私は' + WISH + TAIL,
    '彼は' + TARGET + 'を望んでいます。' + PREMISES[0] + '、私は' + WISH + TAIL,
    '私は' + TARGET + 'を望んでいます。私は川辺で過ごす時間を望んでいます。' + PREMISES[0] + '、私は' + WISH + TAIL,
))
def test_missing_author_or_unique_referent_is_not_supplied(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('kind', ('reference_scalar', 'reference_utf8', 'scope', 'author', 'plan'))
def test_tampered_original_bindings_are_rejected_before_editing(kind):
    text = '私は' + TARGET + 'を望んでいます。' + PREMISES[0] + '、私は' + WISH + TAIL
    out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    meaning, plan = out.source_meaning, out.artifact_plan
    if kind.startswith('reference_'):
        ref, = meaning.nominal_references
        field = 'antecedent_scalar_span' if kind.endswith('scalar') else 'antecedent_utf8_span'
        a, b = getattr(ref, field)
        meaning = replace(meaning, nominal_references=(replace(ref, **{field: (a + 1, b)}),))
    elif kind == 'scope':
        meaning = replace(meaning, expression_scopes=())
    elif kind == 'author':
        first = meaning.graph.nodes[0]
        meaning = replace(meaning, graph=replace(meaning.graph,
            nodes=(replace(first, value=first.value.replace('私は', '僕は', 1)), *meaning.graph.nodes[1:])))
    else:
        plan = replace(plan, duties=(replace(plan.duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT'), *plan.duties[1:]))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_format_rights_do_not_change_when_the_topic_is_omitted(tier):
    text = '私は' + TARGET + 'を望んでいるかもしれません。' + PREMISES[0] + '、私は' + WISH + TAIL
    expected = '私は、' + TARGET + 'を望んでいるかもしれません。' + PREMISES[0] + '、' + WISH + TAIL
    assert_body(text, expected, tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text, tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE
        assert out.reason_codes == ('format_choice_not_admitted',)


class Metrics:
    profile_id = 'synthetic-linked-direct-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, size):
        width = len(text) * size
        return TextMeasurement(width, 0, -.8 * size, width, .2 * size)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_exact_edited_body_reaches_the_unchanged_measured_layout(ratio):
    text = '私は' + TARGET + 'を大切にしたいかもしれません。' + PREMISES[0] + '、私は' + WISH + TAIL
    expected = '私は、' + TARGET + 'を大切にしたいかもしれません。' + PREMISES[0] + '、' + WISH + TAIL
    out = assert_body(text, expected)
    c = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == c['piece_text_hash']
