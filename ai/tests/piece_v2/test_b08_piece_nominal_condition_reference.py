"""Whole nominal conditions use the existing unique prior-object resolver.

Synthetic sources only. A referent does not assert that its condition is met,
transfer its owner's stance, or license a new predicate or public contract.
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
WISH = '考えをゆっくり整理したいです。'
TAIL = 'まだ、毎朝続けるかは決めていません。'


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'nominal-condition', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'nominal-condition', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free'):
    out = outcome(text, tier=tier)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert artifact.piece_text == expected
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
    assert realize_piece_artifact(meaning, plan, tier=tier, requested_format=None) == artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    source = PieceSourceSnapshot('synthetic-owner', 'nominal-condition', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, tier=tier)
    assert candidate == artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression and not plan.declaration_eligible
    return out


@pytest.mark.parametrize('marker', ('なら', 'ならば'))
@pytest.mark.parametrize('determiner', ('その', 'この'))
@pytest.mark.parametrize('first,body', (
    ('私は' + TARGET + 'を大切にしていました。', '私は、' + TARGET + 'を大切にしていました。'),
    ('私にとって' + TARGET + 'が大切です。', '私にとって、' + TARGET + 'が大切です。'),
    ('私が望んでいるのは、' + TARGET + 'です。', '私は、' + TARGET + 'を望んでいる。'),
))
def test_complete_nominal_condition_keeps_its_unique_object_and_reservation(marker, determiner, first, body):
    premise = determiner + '時間' + marker
    text = first + premise + '、私は' + WISH + TAIL
    out = assert_body(text, body + premise + '、' + WISH + TAIL)
    ref, = out.source_meaning.nominal_references
    scope, = out.source_meaning.expression_scopes
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert text[slice(*ref.antecedent_scalar_span)] == TARGET
    assert text[slice(*ref.reference_scalar_span)] == determiner + '時間'
    assert scope.relation == 'SOURCE_EXPLICIT_CONDITION' and scope.marker == marker
    assert text[slice(*scope.scope_scalar_span)] == premise
    assert ref.reference_scalar_span[0] == scope.scope_scalar_span[0]
    assert ref.reference_scalar_span[1] == scope.scope_scalar_span[1] - len(marker)
    assert out.artifact_plan.duties[1].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'


@pytest.mark.parametrize('target,head', (
    ('自分の言葉で日々を記して読み返すこと', 'こと'),
    ('長く自分の手元に置いてきたもの', 'もの'),
    ('🌱を窓辺で静かに眺めて過ごす時間', '時間'),
))
@pytest.mark.parametrize('predicate', ('望んでいませんでした', '選びたくなかったかもしれません'))
def test_the_referents_past_negation_or_uncertainty_is_not_the_conditions_fulfillment(target, head, predicate):
    first = '僕は' + target + 'を' + predicate + '。'
    premise = 'その' + head + 'なら'
    out = assert_body(first + premise + '、僕は答えを急ぎたくないです。' + TAIL,
        '僕は、' + target + 'を' + predicate + '。' + premise + '、答えを急ぎたくないです。' + TAIL)
    assert out.source_meaning.expression_scopes[0].relation == 'SOURCE_EXPLICIT_CONDITION'
    assert {e.relation for e in out.source_meaning.graph.edges} == {'SOURCE_ORDER', 'SOURCE_BOUND_NOMINAL_REFERENCE'}


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_existing_explicit_author_spelling_owns_the_whole_expression(speaker):
    first = speaker + 'は' + TARGET + 'を大切にしています。'
    assert_body(first + 'その時間ならば、' + speaker + 'は' + WISH + TAIL,
        speaker + 'は、' + TARGET + 'を大切にしています。その時間ならば、' + WISH + TAIL)


@pytest.mark.parametrize('separator', ('、', '，', ','))
def test_source_separator_and_whitespace_do_not_move_original_reference_spans(separator):
    target = '私の友人の秋山さんと🌱を静かに眺める時間'
    text = '\t私は' + target + 'を望んでいました。\t　その時間ならば' + separator + '\t私は' + WISH + TAIL
    out = assert_body(text, '私は、私の友人と🌱を静かに眺める時間を望んでいました。その時間ならば、' + WISH + TAIL)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target
    assert out.source_meaning.envelope.raw_utf8 == text.encode()
    assert '秋山' not in out.artifact.piece_text


@pytest.mark.parametrize('expression,realized', (
    ('私は机で紙を折ることを選びたい。', '私は机で紙を折ることを選びたい。'),
    ('私は机で紙を折ることを望んでいなかったかもしれません。', '私は机で紙を折ることを望んでいなかったかもしれません。'),
    ('私にとって答えを急がないことが大切です。', '私にとって、答えを急がないことが大切です。'),
    ('私は机で紙を折ることが好きではないかもしれません。', '私は、机で紙を折ることが好きではないかもしれません。'),
))
def test_condition_uses_existing_expression_owners_without_converting_viewpoint_or_predicate(expression, realized):
    first = '私は' + TARGET + 'を大切にしていました。'
    assert_body(first + 'その時間なら、' + expression + TAIL,
        '私は、' + TARGET + 'を大切にしていました。その時間なら、' + realized + TAIL)


@pytest.mark.parametrize('gap', ('\n', '\r\n'))
def test_reference_binding_does_not_override_existing_direct_author_line_boundary(gap):
    first = '私は' + TARGET + 'を大切にしていました。'
    assert_body(first + gap + 'その時間なら、私は' + WISH + TAIL,
        '私は、' + TARGET + 'を大切にしていました。その時間なら、私は、' + WISH + TAIL)


def test_an_explicit_different_author_is_kept_not_inferred_from_the_antecedent():
    first = '私は' + TARGET + 'を大切にしています。'
    assert_body(first + 'その時間なら、僕は' + WISH + TAIL,
        '私は、' + TARGET + 'を大切にしています。その時間なら、僕は、' + WISH + TAIL)


@pytest.mark.parametrize('text', (
    'その時間なら、私は' + WISH + TAIL,
    '私は' + TARGET + 'を大切にしています。私は川辺で静かに過ごす時間を望んでいます。その時間なら、私は' + WISH + TAIL,
    '時間の使い方を考えていた。私は' + TARGET + 'を大切にしています。その時間なら、私は' + WISH + TAIL,
    '私は' + TARGET + 'を大切にしています。そのものなら、私は' + WISH + TAIL,
    '私は' + TARGET + 'を大切にしています。その長い時間なら、私は' + WISH + TAIL,
    '私は' + TARGET + 'を大切にしています。その時間ならでは、私は' + WISH + TAIL,
    '私は' + TARGET + 'を大切にしています。その時間なら私は' + WISH + TAIL,
))
def test_unproven_or_partial_condition_referents_are_not_guessed(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('kind', ('scalar', 'utf8', 'target', 'condition', 'plan'))
def test_original_binding_and_conditional_plan_cannot_be_forged(kind):
    text = '私は' + TARGET + 'を大切にしています。その時間なら、私は' + WISH + TAIL
    out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    if kind in ('scalar', 'utf8', 'target'):
        ref, = meaning.nominal_references
        field = 'reference_scalar_span' if kind == 'scalar' else 'reference_utf8_span' if kind == 'utf8' else 'antecedent_scalar_span'
        a, b = getattr(ref, field)
        meaning = replace(meaning, nominal_references=(replace(ref, **{field: (a + 1, b)}),))
    elif kind == 'condition':
        scope, = meaning.expression_scopes
        meaning = replace(meaning, expression_scopes=(replace(scope, relation='SOURCE_EXPLICIT_REASON'),))
    else:
        plan = replace(plan, duties=(plan.duties[0], replace(plan.duties[1], operation='KEEP_COMPLETE_SOURCE_CONTEXT'), *plan.duties[2:]))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_a_conditional_expression_does_not_become_an_isolated_quote_or_declaration(tier):
    text = '私は' + TARGET + 'を大切にしています。その時間なら、私は' + WISH + TAIL
    assert_body(text, '私は、' + TARGET + 'を大切にしています。その時間なら、' + WISH + TAIL, tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text, tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE
        assert out.reason_codes == ('format_choice_not_admitted',)


class Metrics:
    profile_id = 'synthetic-nominal-condition-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, size):
        width = len(text) * size
        return TextMeasurement(width, 0, -.8 * size, width, .2 * size)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_conditional_body_reaches_existing_measured_layout(ratio):
    text = '私は' + TARGET + 'を大切にしていました。その時間なら、私は' + WISH + TAIL
    out = assert_body(text, '私は、' + TARGET + 'を大切にしていました。その時間なら、' + WISH + TAIL)
    c = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == c['piece_text_hash']


def test_existing_case_marked_compound_scope_is_not_reinterpreted_as_a_bare_condition():
    # The old particle-based resolver already owns the first operand here.
    # Keep the whole compound premise, not a shortened bare-reference scope.
    text = '私は' + TARGET + 'を大切にしています。その時間と別の予定なら、私は' + WISH + TAIL
    out = assert_body(text, '私は、' + TARGET + 'を大切にしています。その時間と別の予定なら、' + WISH + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert text[slice(*scope.scope_scalar_span)] == 'その時間と別の予定なら'


@pytest.mark.parametrize('expression,realized', (
    ('私はその時間を大切にしたいかもしれません。', '私はその時間を大切にしたいかもしれません。'),
    ('私はその時間が好きではなかったかもしれません。', '私は、その時間が好きではなかったかもしれません。'),
    ('私にとってその時間が大切です。', '私にとって、その時間が大切です。'),
))
def test_scope_and_expression_mentions_bind_independently_to_the_same_original_object(expression, realized):
    first = '私は' + TARGET + 'を望んでいませんでした。'
    text = first + 'その時間なら、' + expression + TAIL
    out = assert_body(text, '私は、' + TARGET + 'を望んでいませんでした。その時間なら、' + realized + TAIL)
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert [r.antecedent_node_id for r in refs] == ['piece:s1', 'piece:s1']
    assert refs[0].antecedent_scalar_span == refs[1].antecedent_scalar_span
    assert refs[0].reference_scalar_span[1] < refs[1].reference_scalar_span[0]
    assert all(text[slice(*r.reference_scalar_span)] == 'その時間' for r in refs)


@pytest.mark.parametrize('following', (
    'その時間なら、考えを整理したい。',
    'その時間なら、彼は考えを整理したい。',
    'あの時間なら、私は考えを整理したい。',
))
def test_a_conditional_marker_does_not_supply_an_omitted_author_or_new_determiner(following):
    out = outcome('私は' + TARGET + 'を大切にしています。' + following + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


def test_a_later_mention_still_points_to_the_original_object_not_the_condition():
    text = '私は' + TARGET + 'を大切にしていました。その時間なら、私は' + WISH + '私はその時間が好きかもしれません。' + TAIL
    out = assert_body(text, '私は、' + TARGET + 'を大切にしていました。その時間なら、' + WISH + '私は、その時間が好きかもしれません。' + TAIL)
    assert [r.antecedent_node_id for r in out.source_meaning.nominal_references] == ['piece:s1', 'piece:s1']


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_resolving_a_short_condition_does_not_lower_the_existing_text_envelope(tier):
    # Boundary fixture only, not a proposed product example or padded fallback.
    # The unchanged lower bound is 24: the 25-character complete body
    # remains available by declining an optional 3-character author omission.
    text = '私はものを選びたい。そのものなら、私は寝たい。'
    body = '私は、ものを選びたい。そのものなら、私は、寝たい。'
    assert len(body) == 25
    assert_body(text, body, tier=tier)
    # This whole source is too short even with both explicit topics retained.
    short = '私はものが好き。そのものなら、私は寝たい。'
    assert len('私は、ものが好き。そのものなら、私は、寝たい。') == 23
    out = outcome(short, tier=tier)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_not_eligible',)
    assert out.artifact is None
