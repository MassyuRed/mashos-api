"""A proved initial prospective time topic is not an unresolved nominal object.

Use the existing source scope and live Piece consumer; do not infer an author,
referent, date, continuation or new commitment from a prospective word.
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
from piece_v2_expression import _REFERENCE
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

TARGET = '朝に窓辺で葉の形をゆっくり眺める時間'
TAIL = 'ただ、毎日続けるかはまだ決めていない。'


def outcome(text, *, tier='free', requested_format=None):
    s = PieceSourceSnapshot('synthetic-owner', 'prospective-topic', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'prospective-topic', s, s.owner_id, s.saved_input_id, s.source_version,
        tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    m, plan = out.source_meaning, out.artifact_plan
    assert m.envelope.raw_utf8 == text.encode()
    for node, ev in zip(m.graph.nodes, m.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    assert tuple(n for b in plan.block_node_ids for n in b) == tuple(n.node_id for n in m.graph.nodes)
    assert compile_piece_artifact_plan(m) == plan
    saved = asdict(m), asdict(plan)
    assert realize_piece_artifact(m, plan, tier=tier, requested_format=requested_format) == out.artifact
    assert saved == (asdict(m), asdict(plan))
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'prospective-topic', 'v1', text),
        authenticated_owner_id='synthetic-owner', tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    for scope in m.expression_scopes:
        assert text[slice(*scope.scope_scalar_span)].encode() == text.encode()[slice(*scope.scope_utf8_span)]
        assert text[slice(*scope.expression_scalar_span)].encode() == text.encode()[slice(*scope.expression_utf8_span)]
    return out


@pytest.mark.parametrize('marker', ('は', 'も'))
@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_prospective_topic_and_explicit_author_keep_the_whole_reservation(marker, speaker):
    prefix = 'これから' + marker
    text = prefix + '、' + speaker + 'が大切にしたいのは、' + TARGET + 'です。' + TAIL
    out = assert_body(text, prefix + '、' + speaker + 'は' + TARGET + 'を大切にしたい。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == 'SOURCE_EXPLICIT_TIME_CONTEXT' and scope.marker == marker
    assert text[slice(*scope.scope_scalar_span)] == prefix
    assert out.source_meaning.nominal_references == ()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('prefix', ('これからは、', 'これからも、'))
@pytest.mark.parametrize('predicate', ('大切にしたい', '大切にしたくない', '望んでいるかもしれない', '望んでいないとは限らない'))
@pytest.mark.parametrize('construction', ('focal', 'direct'))
def test_complete_predicate_negation_and_modality_are_not_changed(prefix, predicate, construction):
    expression = ('私が' + predicate + 'のは、' + TARGET + 'です。' if construction == 'focal'
                  else '私は' + TARGET + 'を' + predicate + '。')
    assert_body(prefix + expression + TAIL, prefix + '私は' + TARGET + 'を' + predicate + '。' + TAIL)


@pytest.mark.parametrize('prefix', ('これからは、', 'これからも、'))
@pytest.mark.parametrize('predicate,finite', (
    ('大切な', '大切です'), ('必要ではない', '必要ではない'),
    ('大切かもしれない', '大切かもしれない'), ('必要とは限らない', '必要とは限らない'),
))
def test_value_viewpoint_remains_distinct_from_time(prefix, predicate, finite):
    text = prefix + '私にとって' + predicate + 'のは、' + TARGET + 'です。' + TAIL
    out = assert_body(text, prefix + '私にとって' + TARGET + 'が' + finite + '。' + TAIL)
    assert len(out.source_meaning.personal_evaluations) == 1
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('prefix', ('これからは、', 'これからも、'))
def test_bound_nominal_reference_is_independent_of_the_time_topic(prefix):
    first = '私が大切にしたいのは、' + TARGET + 'です。'
    second = prefix + '私にとってその時間が必要とは限らない。'
    out = assert_body(first + second + TAIL,
        '私は、' + TARGET + 'を大切にしたい。' + second + TAIL)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert (first + second + TAIL)[slice(*ref.reference_scalar_span)] == 'その時間'
    assert out.source_meaning.personal_evaluations[0].commitment == 'NON_UNIVERSAL'


@pytest.mark.parametrize('separator', ('、', '，', ',', '、\t', '、　'))
def test_source_scope_coordinates_survive_written_separator_and_unicode(separator):
    target = '私の友人の三浦さんと🌿の形を静かに眺める時間'
    text = '\tこれからも' + separator + '僕が大切にしたいのは、' + target + 'です。\r\n　' + TAIL
    out = assert_body(text, 'これからも、僕は私の友人と🌿の形を静かに眺める時間を大切にしたい。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.scope_scalar_span == (1, 6)
    assert scope.scope_utf8_span != scope.scope_scalar_span
    assert out.source_meaning.sentences[1].source_start == text.index('ただ')


def test_preceding_context_and_later_intention_keep_source_order():
    before = '毎日続けるかはまだ決めていない。'
    expression = 'これからは、私が大切にしたいのは、' + TARGET + 'です。'
    after = '私は葉の色も静かに観察したい。'
    out = assert_body(before + expression + after,
        before + 'これからは、私は' + TARGET + 'を大切にしたい。私は、葉の色も静かに観察したい。')
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3'),)


@pytest.mark.parametrize('text', (
    'これからは、私が望んでいるのは、その時間です。',
    'これからも、私にとってその時間が必要です。',
    'これからは、私が大切にしたいのは、これです。',
    'これからも、私はこれを大切にしたい。',
    '私が大切にしたいのは、これからは静かに眺める時間です。',
    '私にとってこれからも続けることが大切です。',
    'これからは、私が望んでいるのは、これから毎日選ぶものです。',
    'これからも、私にとって必要なのは、そのこととこの時間です。',
    'これからは、彼が大切にしたいのは、' + TARGET + 'です。',
    'これからも、大切にしたいのは、' + TARGET + 'です。',
    'これからは、私が望んでいると彼は話した。',
    'これからも、私は窓辺で葉を眺めたい。',
    'これからは私が大切にしたいのは、' + TARGET + 'です。',
    'これからの、私が大切にしたいのは、' + TARGET + 'です。',
    'それからは、私が大切にしたいのは、' + TARGET + 'です。',
    'あれからも、私が大切にしたいのは、' + TARGET + 'です。',
    'ここからは、私が大切にしたいのは、' + TARGET + 'です。',
    'あれこれからは、私が大切にしたいのは、' + TARGET + 'です。',
    'ただ、これからは、私が大切にしたいのは、' + TARGET + 'です。',
))
def test_time_scope_does_not_infer_nominal_targets_or_admit_other_grammars(text):
    out = outcome(text + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('tail', (
    'これは大切だ。', 'そのことはまだ決めていない。',
    'ただ、これから取り出すものはまだ決めていない。',
    'ただ、これからは続けるかはまだ決めていない。',
))
def test_other_sentence_references_are_not_covered_by_a_proved_time_scope(tail):
    text = 'これからも、私が大切にしたいのは、' + TARGET + 'です。' + tail
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('text', ('これからは。', 'これからも、続けたい。', 'これからは、まだ決めていない。'))
def test_time_alone_supplies_no_piece_meaning_or_author(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_time_and_uncertainty_cannot_be_excerpted_as_a_quote_or_pledge(tier):
    text = 'これからは、私が大切にしたいのは、' + TARGET + 'です。' + TAIL
    assert_body(text, 'これからは、私は' + TARGET + 'を大切にしたい。' + TAIL, tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text, tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('mutation', ('scalar', 'utf8', 'marker', 'relation', 'expression', 'node', 'order', 'declaration'))
def test_only_recomputed_source_time_scope_can_authorize_the_token(mutation):
    text = 'これからは、私が大切にしたいのは、' + TARGET + 'です。' + TAIL
    out = assert_body(text, 'これからは、私は' + TARGET + 'を大切にしたい。' + TAIL)
    m, plan = out.source_meaning, out.artifact_plan
    scope, = m.expression_scopes
    if mutation == 'scalar': scope = replace(scope, scope_scalar_span=(0, 4))
    elif mutation == 'utf8': scope = replace(scope, scope_utf8_span=(0, 4))
    elif mutation == 'marker': scope = replace(scope, marker='も')
    elif mutation == 'relation': scope = replace(scope, relation='SOURCE_EXPLICIT_REASON')
    elif mutation == 'expression': scope = replace(scope, expression_scalar_span=(0, len(text)))
    elif mutation == 'node':
        m = replace(m, graph=replace(m.graph, nodes=(replace(m.graph.nodes[0], value=m.graph.nodes[0].value.replace('これから', '')), *m.graph.nodes[1:])))
    elif mutation == 'order': plan = replace(plan, block_node_ids=(('piece:s2', 'piece:s1'),))
    else: plan = replace(plan, declaration_eligible=True)
    m = replace(m, expression_scopes=(scope,))
    with pytest.raises(ValueError):
        realize_piece_artifact(m, plan, tier='free', requested_format=None)


def test_general_reference_detector_is_unchanged():
    assert _REFERENCE.search('これからは')[0] == 'これから'
    assert _REFERENCE.search('それからも')[0] == 'それから'


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_canonical_text_reaches_both_existing_layouts(ratio):
    text = 'これからは、私が大切にしたいのは、' + TARGET + 'です。' + TAIL
    out = assert_body(text, 'これからは、私は' + TARGET + 'を大切にしたい。' + TAIL)
    class Metrics:
        profile_id = 'synthetic-prospective-topic-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']


@pytest.mark.parametrize('prefix', ('これからは、', 'これからも、'))
def test_polite_non_universality_uses_its_existing_finite_construction(prefix):
    sentence = prefix + '私にとって' + TARGET + 'が必要とは限りません。'
    out = assert_body(sentence + TAIL, sentence + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert frame.commitment == 'NON_UNIVERSAL'


@pytest.mark.parametrize('prefix', ('これからは、', 'これからも、'))
def test_unadmitted_polite_nominalization_is_not_created_by_time(prefix):
    text = prefix + '私にとって必要とは限りませんのは、' + TARGET + 'です。' + TAIL
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('marker', ('は', 'も'))
def test_short_scoped_body_does_not_bypass_the_content_envelope(marker):
    text = 'これから' + marker + '、私が望んでいるのは、休む時間です。'
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.reason_codes == ('format_not_eligible',)
