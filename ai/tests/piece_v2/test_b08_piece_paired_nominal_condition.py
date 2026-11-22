"""Synthetic paired conditional referents retain both objects and one author.

No new predicate, inferred subject, relation, activation or product acceptance.
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

TIME = '一人で静かに考えを整理する時間'
ACT = '考えを短くノートに残すこと'
TAIL = 'まだ、毎日続けるかは決めていません。'
WISH = '無理なく続けたいです。'


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'paired-condition', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'paired-condition', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def intro(speaker='私'):
    return speaker + 'は' + TIME + 'を大切にしています。' + speaker + 'は' + ACT + 'を選びたいです。'


def text(premise='その時間とこのことなら', speaker='私'):
    return intro(speaker) + premise + '、' + speaker + 'は' + WISH + TAIL


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
    candidate = generate_piece_candidate(PieceSourceSnapshot('synthetic-owner', 'paired-condition', 'v1', source),
                                         authenticated_owner_id='synthetic-owner', tier=tier)
    assert candidate == artifact.as_candidate()
    assert artifact.eligible_formats == ('short_essay',)
    assert not out.automatic_progression and not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('marker', ('なら', 'ならば'))
@pytest.mark.parametrize('joiner', ('と', 'と、', 'と，\t', 'と,　'))
@pytest.mark.parametrize('heads', (('その時間', 'このこと'), ('このこと', 'その時間')))
def test_two_complete_conditional_operands_keep_their_order_and_source_targets(marker, joiner, heads):
    premise = joiner.join(heads) + marker
    body = '私は、' + TIME + 'を大切にしています。' + ACT + 'を選びたいです。' + premise + '、' + WISH + TAIL
    out = assert_body(text(premise), body)
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert [text(premise)[slice(*r.reference_scalar_span)] for r in refs] == list(heads)
    assert [r.antecedent_node_id for r in refs] == (['piece:s1', 'piece:s2'] if heads[0].endswith('時間') else ['piece:s2', 'piece:s1'])
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == 'SOURCE_EXPLICIT_CONDITION'
    assert text(premise)[slice(*scope.scope_scalar_span)] == premise
    assert len([e for e in out.source_meaning.graph.edges if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']) == 2


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_a_written_author_is_shared_not_guessed_or_normalized(speaker):
    body = speaker + 'は、' + TIME + 'を大切にしています。' + ACT + 'を選びたいです。その時間とこのことなら、' + WISH + TAIL
    assert_body(text(speaker=speaker), body)


@pytest.mark.parametrize('first_predicate,second_predicate', (
    ('望んでいませんでした', '選びたくなかったかもしれません'),
    ('大切にしていたとは限りません', '望んでいない'),
    ('選びたかったです', '大切にしたくないです'),
))
def test_past_negative_and_modal_referents_do_not_assert_fulfillment(first_predicate, second_predicate):
    source = '私は' + TIME + 'を' + first_predicate + '。私は' + ACT + 'を' + second_predicate + '。その時間とこのことなら、私は答えを急ぎたくないです。' + TAIL
    body = '私は、' + TIME + 'を' + first_predicate + '。' + ACT + 'を' + second_predicate + '。その時間とこのことなら、答えを急ぎたくないです。' + TAIL
    assert_body(source, body)


def test_an_explicit_value_viewpoint_is_retained_while_the_following_wish_shares_its_author():
    source = '私にとって' + TIME + 'が大切です。私にとって' + ACT + 'が必要かもしれません。その時間とこのことなら、私は' + WISH + TAIL
    body = '私にとって、' + TIME + 'が大切です。私にとって、' + ACT + 'が必要かもしれません。その時間とこのことなら、' + WISH + TAIL
    assert_body(source, body)


def test_the_third_existing_nominal_head_is_not_a_new_lexical_subject():
    obj = '長く手元で使ってきたもの'
    source = '僕は' + TIME + 'を大切にしていました。僕は' + obj + 'を望んでいませんでした。このものとその時間なら、僕は考えをゆっくり整理したいです。' + TAIL
    body = '僕は、' + TIME + 'を大切にしていました。' + obj + 'を望んでいませんでした。このものとその時間なら、考えをゆっくり整理したいです。' + TAIL
    assert_body(source, body)


@pytest.mark.parametrize('gap', ('\n', '\r\n'))
def test_a_source_line_boundary_declines_only_the_optional_author_edit(gap):
    source = intro() + gap + 'その時間とこのことなら、私は' + WISH + TAIL
    body = '私は、' + TIME + 'を大切にしています。私は、' + ACT + 'を選びたいです。その時間とこのことなら、私は、' + WISH + TAIL
    assert_body(source, body)


@pytest.mark.parametrize('second,third', (('僕', '私'), ('私', '僕'), ('わたし', '私')))
def test_different_literal_speakers_keep_all_explicit_topics(second, third):
    source = '私は' + TIME + 'を大切にしています。' + second + 'は' + ACT + 'を選びたいです。その時間とこのことなら、' + third + 'は' + WISH + TAIL
    body = '私は、' + TIME + 'を大切にしています。' + second + 'は、' + ACT + 'を選びたいです。その時間とこのことなら、' + third + 'は、' + WISH + TAIL
    assert_body(source, body)


@pytest.mark.parametrize('expression,body', (
    ('私は旅に出る前の鳥みたい。', '私は、旅に出る前の鳥みたい。'),
    ('私は友人が望む場所へ行きたい。', '私は、友人が望む場所へ行きたい。'),
    ('私にとって落ち着いて考えることが大切です。', '私にとって、落ち着いて考えることが大切です。'),
    ('私はこのことを大切にしたい。', '私はこのことを大切にしたい。'),
))
def test_other_constructions_do_not_acquire_the_simple_wish_topic_edit(expression, body):
    source = intro() + 'その時間とこのことなら、' + expression + TAIL
    expected = '私は、' + TIME + 'を大切にしています。私は、' + ACT + 'を選びたいです。その時間とこのことなら、' + body + TAIL
    assert_body(source, expected)


def test_intervening_context_is_kept_and_does_not_certify_adjacent_authorship():
    source = intro() + '今日は机を片付けた。その時間とこのことなら、私は' + WISH + TAIL
    body = '私は、' + TIME + 'を大切にしています。私は、' + ACT + 'を選びたいです。今日は机を片付けた。その時間とこのことなら、私は、' + WISH + TAIL
    assert_body(source, body)


def test_original_utf8_ranges_survive_explicit_role_publicization():
    target = '私の友人の秋山さんと🌱を眺める時間'
    source = text().replace(TIME, target)
    body = '私は、私の友人と🌱を眺める時間を大切にしています。' + ACT + 'を選びたいです。その時間とこのことなら、' + WISH + TAIL
    out = assert_body(source, body)
    assert source[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target
    assert '秋山' not in out.artifact.piece_text


@pytest.mark.parametrize('following', (
    'その時間とこの時間なら、私は' + WISH,
    'その時間とあのことなら、私は' + WISH,
    'その時間とこのものなら、私は' + WISH,
    'その時間とこのこととその時間なら、私は' + WISH,
    'その時間と長いこのことなら、私は' + WISH,
    'その時間かこのことなら、私は' + WISH,
    'その時間よりこのことなら、私は' + WISH,
    'その時間とこのことならでは、私は' + WISH,
    'その時間とこのことなら、' + WISH,
    'その時間とこのことなら、彼は' + WISH,
))
def test_unsupported_pairs_operators_or_authors_are_not_guessed(following):
    out = outcome(intro() + following + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('source', (
    'その時間とこのことなら、私は' + WISH + TAIL,
    intro() + '私は森で過ごす時間を選びたい。その時間とこのことなら、私は' + WISH + TAIL,
    'ことの始まりを考えていた。' + text(),
))
def test_missing_or_competing_antecedents_stay_unavailable(source):
    assert outcome(source).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('damage', ('reference', 'range', 'utf8', 'edge', 'condition', 'plan'))
def test_neither_reference_nor_the_conditional_plan_can_be_forged(damage):
    out = outcome(text()); assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    first, second = meaning.nominal_references
    if damage == 'reference':
        meaning = replace(meaning, nominal_references=(first,))
    elif damage in ('range', 'utf8'):
        field = 'reference_scalar_span' if damage == 'range' else 'reference_utf8_span'
        a, b = getattr(second, field)
        meaning = replace(meaning, nominal_references=(first, replace(second, **{field: (a + 1, b)})))
    elif damage == 'edge':
        meaning = replace(meaning, graph=replace(meaning.graph, edges=meaning.graph.edges[:-1]))
    elif damage == 'condition':
        scope, = meaning.expression_scopes
        meaning = replace(meaning, expression_scopes=(replace(scope, relation='SOURCE_EXPLICIT_REASON'),))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1',), ('piece:s2', 'piece:s3', 'piece:s4')))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_paired_conditions_remain_complete_short_essays(tier):
    body = '私は、' + TIME + 'を大切にしています。' + ACT + 'を選びたいです。その時間とこのことなら、' + WISH + TAIL
    assert_body(text(), body, tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text(), tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE
        assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_the_same_canonical_body_reaches_existing_b9_layout(ratio):
    out = outcome(text()); assert out.status == EngineStatus.GENERATED, out.as_body_free()
    candidate = out.artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-paired-condition-not-native'
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


def test_topic_omission_changes_words_only_not_the_source_or_plan(monkeypatch):
    import cocolon_meaning_experience_engine.piece_v1c as author
    out = outcome(text()); assert out.status == EngineStatus.GENERATED
    frozen = asdict(out.source_meaning), asdict(out.artifact_plan)
    monkeypatch.setattr(author, '_paired_self_continuations', lambda *args: frozenset())
    full = realize_piece_artifact(out.source_meaning, out.artifact_plan, tier='free', requested_format=None)
    assert full.piece_text == '私は、' + TIME + 'を大切にしています。私は、' + ACT + 'を選びたいです。その時間とこのことなら、私は、' + WISH + TAIL
    assert (asdict(out.source_meaning), asdict(out.artifact_plan)) == frozen
