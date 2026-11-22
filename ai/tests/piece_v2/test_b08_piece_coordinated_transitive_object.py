"""Synthetic two-reference transitive objects retain both operands and author.

The existing predicate, scope, source resolver and image contracts remain owners.
No unmarked author, comparison winner, missing referent or fulfillment is inferred.
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

TIME = '朝に窓辺で静かに本を読む時間'
ACT = '読み終えた後に考えをノートに残すこと'
THING = '長く手元で使ってきたもの'
TAIL = 'まだ毎日続けるかどうかは決めていない。'


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'coordinated-object', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'coordinated-object', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def intro(speaker='私', first=TIME, second=ACT):
    return (speaker + 'が大切にしたいのは、' + first + 'です。'
            + speaker + 'が選びたいのは、' + second + 'です。')


def text(predicate='大切にしたい', pair='その時間とこのこと', speaker='私'):
    return intro(speaker) + speaker + 'は' + pair + 'を' + predicate + '。' + TAIL


def expected(predicate='大切にしたい', pair='その時間とこのこと', speaker='私'):
    return (speaker + 'は、' + TIME + 'を大切にしたい。'
            + ACT + 'を選びたい。' + pair + 'を' + predicate + '。' + TAIL)


def assert_body(source, body, *, tier='free'):
    out = outcome(source, tier=tier)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert artifact.piece_text == body
    assert artifact.piece_text_hash == hashlib.sha256(body.encode()).hexdigest()
    assert meaning.envelope.raw_utf8 == source.encode()
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for block in plan.block_node_ids for n in block) == tuple(n.node_id for n in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert source[ev.scalar_start:ev.scalar_end] == node.value
        assert source.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    for ref in meaning.nominal_references:
        for a, b in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                     (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert source[slice(*a)].encode() == source.encode()[slice(*b)]
    frozen = asdict(meaning), asdict(plan)
    assert realize_piece_artifact(meaning, plan, tier=tier, requested_format=None) == artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    candidate = generate_piece_candidate(PieceSourceSnapshot(
        'synthetic-owner', 'coordinated-object', 'v1', source),
        authenticated_owner_id='synthetic-owner', tier=tier)
    assert candidate == artifact.as_candidate()
    assert artifact.eligible_formats == ('short_essay',)
    assert not out.automatic_progression and not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('pair', ('その時間とこのこと', 'このこととその時間',
                                  'その時間と、このこと', 'このことと，\tその時間',
                                  'その時間と,　このこと'))
def test_both_ordered_operands_share_one_transitive_predicate(pair):
    out = assert_body(text(pair=pair), expected(pair=pair))
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert [r.antecedent_node_id for r in refs] == (
        ['piece:s1', 'piece:s2'] if pair.startswith('その時間') else ['piece:s2', 'piece:s1'])
    assert {text(pair=pair)[slice(*r.reference_scalar_span)] for r in refs} == {'その時間', 'このこと'}
    assert len([e for e in out.source_meaning.graph.edges
                if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']) == 2


@pytest.mark.parametrize('predicate', (
    '大切にしている', '大切にしたくない', '望んでいる', '望んでいない',
    '選びたい', '選びたくない', '大切にしています', '望んでいませんでした',
    '大切にしたかったです', '選びたくなかったかもしれません',
    '大切にしていたとは限りません',
))
def test_the_existing_predicate_time_register_negation_and_modal_are_unchanged(predicate):
    assert_body(text(predicate), expected(predicate))


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_only_the_same_written_author_is_shared(speaker):
    assert_body(text(speaker=speaker), expected(speaker=speaker))


@pytest.mark.parametrize('first,second,pair', (
    (TIME, THING, 'このものとその時間'),
    (ACT, THING, 'そのこととこのもの'),
))
def test_all_existing_nominal_heads_keep_their_distinct_antecedents(first, second, pair):
    source = intro(first=first, second=second) + '私は' + pair + 'を望んでいない。' + TAIL
    assert_body(source, '私は、' + first + 'を大切にしたい。' + second
                + 'を選びたい。' + pair + 'を望んでいない。' + TAIL)


@pytest.mark.parametrize('scope', ('予定が合うなら', '予定が合うならば',
                                   '予定が合うので', '予定は合わないけれど',
                                   '以前は', '今も'))
def test_written_outer_scope_is_not_a_third_argument_or_an_unconditional_pledge(scope):
    expression = '私はその時間とこのことを選びたくなかったかもしれません。'
    source = intro() + scope + '、' + expression + TAIL
    body = ('私は、' + TIME + 'を大切にしたい。私は、' + ACT
            + 'を選びたい。' + scope + '、' + expression + TAIL)
    out = assert_body(source, body)
    scoped, = out.source_meaning.expression_scopes
    assert source[slice(*scoped.scope_scalar_span)] == scope
    assert source[slice(*scoped.expression_scalar_span)] == expression


@pytest.mark.parametrize('separator', ('\n', '\r\n', '今日は机を片付けた。'))
def test_a_discourse_boundary_keeps_the_explicit_topics(separator):
    source = intro() + separator + '私はその時間とこのことを大切にしたい。' + TAIL
    context = separator if separator.endswith('。') else ''
    body = ('私は、' + TIME + 'を大切にしたい。私は、' + ACT + 'を選びたい。'
            + context + '私は、その時間とこのことを大切にしたい。' + TAIL)
    assert_body(source, body)


@pytest.mark.parametrize('second,third', (('僕', '私'), ('私', '僕'), ('わたし', '私')))
def test_different_speakers_do_not_gain_author_aliases(second, third):
    source = ('私が大切にしたいのは、' + TIME + 'です。'
              + second + 'が選びたいのは、' + ACT + 'です。'
              + third + 'はその時間とこのことを大切にしたい。' + TAIL)
    body = ('私は、' + TIME + 'を大切にしたい。' + second + 'は、' + ACT
            + 'を選びたい。' + third + 'は、その時間とこのことを大切にしたい。' + TAIL)
    assert_body(source, body)


def test_explicit_value_viewpoints_are_kept_not_rewritten_as_self_topics():
    source = ('私にとって' + TIME + 'が大切です。私にとって' + ACT
              + 'が必要かもしれません。私はその時間とこのことを望んでいない。' + TAIL)
    body = ('私にとって、' + TIME + 'が大切です。私にとって、' + ACT
            + 'が必要かもしれません。その時間とこのことを望んでいない。' + TAIL)
    assert_body(source, body)


def test_direct_antecedents_keep_their_written_state_and_rejection():
    source = ('私は' + TIME + 'を望んでいませんでした。私は' + ACT
              + 'を大切にしています。私はこのこととその時間を選びたくないです。' + TAIL)
    body = ('私は、' + TIME + 'を望んでいませんでした。' + ACT
            + 'を大切にしています。このこととその時間を選びたくないです。' + TAIL)
    assert_body(source, body)


def test_original_name_role_and_utf8_ranges_precede_publicization():
    target = '私の友人の秋山さんと🌱を眺める時間'
    source = text().replace(TIME, target)
    body = expected().replace(TIME, '私の友人と🌱を眺める時間')
    out = assert_body(source, body)
    assert source[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target
    assert '秋山' not in out.artifact.piece_text


@pytest.mark.parametrize('expression', (
    'その時間とこのことを大切にしたい。',
    '彼はその時間とこのことを大切にしたい。',
    '私はその時間とこの時間を大切にしたい。',
    '私はその時間とこのものを大切にしたい。',
    '私はその時間とあのことを大切にしたい。',
    '私はその時間と長いこのことを大切にしたい。',
    '私はその時間とこのこととその時間を大切にしたい。',
    '私はその時間よりこのことを大切にしたい。',
    '私はその時間かこのことを大切にしたい。',
    '私はその時間とこのことを振り返った。',
    '私はその時間とこのことを大切にしていますかもしれない。',
    '私が大切にしたいのは、その時間とこのことです。',
))
def test_unwritten_author_unresolved_operand_and_other_constructions_are_not_inferred(expression):
    out = outcome(intro() + expression + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('source', (
    '私はその時間とこのことを大切にしたい。' + TAIL,
    intro() + '私は森で過ごす時間を選びたい。私はその時間とこのことを大切にしたい。' + TAIL,
    'ことの始まりを考えていた。' + text(),
))
def test_missing_or_competing_antecedents_stay_unavailable(source):
    assert outcome(source).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('damage', ('reference', 'target', 'utf8', 'edge', 'plan'))
def test_the_second_operand_cannot_be_forged_or_detached(damage):
    out = outcome(text()); assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    first, second = meaning.nominal_references
    if damage == 'reference':
        meaning = replace(meaning, nominal_references=(first,))
    elif damage in ('target', 'utf8'):
        field = 'antecedent_scalar_span' if damage == 'target' else 'reference_utf8_span'
        a, b = getattr(second, field)
        meaning = replace(meaning, nominal_references=(first, replace(second, **{field: (a + 1, b)})))
    elif damage == 'edge':
        meaning = replace(meaning, graph=replace(meaning.graph, edges=meaning.graph.edges[:-1]))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1',), ('piece:s2', 'piece:s3', 'piece:s4')))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_both_operands_and_context_stay_one_complete_short_essay(tier):
    assert_body(text(), expected(), tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text(), tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE
        assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_the_canonical_body_reaches_the_existing_b9_layout_without_omission(ratio):
    out = outcome(text()); assert out.status == EngineStatus.GENERATED, out.as_body_free()
    candidate = out.artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-coordinated-object-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']


def test_optional_author_omission_does_not_change_the_meaning_or_plan(monkeypatch):
    import cocolon_meaning_experience_engine.piece_v1c as author
    out = outcome(text()); assert out.status == EngineStatus.GENERATED
    frozen = asdict(out.source_meaning), asdict(out.artifact_plan)
    monkeypatch.setattr(author, '_paired_self_continuations', lambda *args: frozenset())
    full = realize_piece_artifact(out.source_meaning, out.artifact_plan, tier='free', requested_format=None)
    assert full.piece_text == ('私は、' + TIME + 'を大切にしたい。私は、' + ACT
                               + 'を選びたい。私は、その時間とこのことを大切にしたい。' + TAIL)
    assert (asdict(out.source_meaning), asdict(out.artifact_plan)) == frozen
