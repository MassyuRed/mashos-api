"""Keep explicit time topics around existing focal predicates and references.

Synthetic inputs only. The temporal topic cannot change predicate tense,
resolve a missing author, pick an ambiguous object or license a declaration.
The current source/plan/author/B9 route remains the sole output route.
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

TIME = '休日に台所でゆっくりお茶をいれる時間'
ACT = '気づいた考えを短く手帳に残すこと'
TAIL = 'まだ毎週続けるかどうかは決めていない。'
TIMES = ('以前は', '以前も', '当時は', '当時も', '今は', '今も', '現在は', '現在も')
PAST = ('大切にしたかった', '大切にしていた', '大切にしたくなかった',
        '望んでいた', '望んでいなかった', '選びたかった', '選びたくなかった')


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'temporal-focal', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'temporal-focal', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode()
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for b in plan.block_node_ids for n in b) == tuple(n.node_id for n in meaning.graph.nodes)
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
    assert realize_piece_artifact(meaning, plan, tier=tier, requested_format=requested_format) == out.artifact
    assert frozen == (asdict(meaning), asdict(plan))
    source = PieceSourceSnapshot('synthetic-owner', 'temporal-focal', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not plan.declaration_eligible
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('topic', TIMES)
@pytest.mark.parametrize('predicate', ('大切にしたい', '望んでいなかった'))
def test_time_particle_does_not_overwrite_the_inner_predicate(topic, predicate):
    text = topic + '、私が' + predicate + 'のは、' + TIME + 'です。'
    out = assert_body(text, topic + '、私は' + TIME + 'を' + predicate + '。')
    scope, = out.source_meaning.expression_scopes
    assert text[slice(*scope.scope_scalar_span)] == topic
    assert scope.marker == topic[-1]
    assert text[slice(*scope.expression_scalar_span)] == '私が' + predicate + 'のは、' + TIME + 'です。'
    assert out.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert out.source_meaning.graph.nodes[0].node_kind == 'PIECE_SOURCE_TIME_SCOPED_EXPRESSION'


@pytest.mark.parametrize('predicate', PAST)
def test_each_existing_past_predicate_keeps_its_time_negation_and_reservation(predicate):
    text = '以前は、私が' + predicate + 'のは、' + TIME + 'です。' + TAIL
    assert_body(text, '以前は、私は' + TIME + 'を' + predicate + '。' + TAIL)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_same_referent_has_distinct_past_and_current_expressions(speaker):
    text = ('以前は、' + speaker + 'が望んでいなかったのは、' + TIME + 'です。'
            '今は、' + speaker + 'はその時間が好きかもしれません。' + TAIL)
    expected = ('以前は、' + speaker + 'は' + TIME + 'を望んでいなかった。'
                '今は、' + speaker + 'はその時間が好きかもしれません。' + TAIL)
    out = assert_body(text, expected)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert text[slice(*ref.antecedent_scalar_span)] == TIME
    frame, = out.source_meaning.personal_evaluations
    assert (frame.temporal_scope, frame.commitment) == ('NONPAST', 'POSSIBLE')
    assert [text[slice(*s.scope_scalar_span)] for s in out.source_meaning.expression_scopes] == ['以前は', '今は']
    assert {e.relation for e in out.source_meaning.graph.edges} == {'SOURCE_ORDER', 'SOURCE_BOUND_NOMINAL_REFERENCE'}


@pytest.mark.parametrize('order', ('focal', 'direct', 'evaluation'))
def test_two_source_objects_are_retained_in_one_temporal_focal_argument(order):
    if order == 'focal':
        intro = '私が望んでいなかったのは、' + TIME + 'です。私が選びたいのは、' + ACT + 'です。'
        first = '私は、' + TIME + 'を望んでいなかった。私は、' + ACT + 'を選びたい。'
    elif order == 'direct':
        intro = '私は' + TIME + 'を望んでいませんでした。私は' + ACT + 'を選びたい。'
        first = '私は、' + TIME + 'を望んでいませんでした。私は、' + ACT + 'を選びたい。'
    else:
        intro = '私にとって' + TIME + 'が大切でした。私は' + ACT + 'が好きです。'
        first = '私にとって、' + TIME + 'が大切でした。私は、' + ACT + 'が好きです。'
    text = intro + '当時も、私が大切にしたかったのは、このこととその時間です。' + TAIL
    out = assert_body(text, first + '当時も、私はこのこととその時間を大切にしたかった。' + TAIL)
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert [r.antecedent_node_id for r in refs] == ['piece:s2', 'piece:s1']
    assert [text[slice(*r.reference_scalar_span)] for r in refs] == ['このこと', 'その時間']


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_time_qualified_source_cannot_be_excerpted_as_a_quote_or_pledge(tier):
    text = '今は、私が選びたいのは、' + TIME + 'です。'
    assert_body(text, '今は、私は' + TIME + 'を選びたい。', tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(text, tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
        assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('separator', ('、', '，', ',', '、\t', '、　'))
def test_whitespace_and_emoji_preserve_original_scope_and_object_coordinates(separator):
    target = '🌱を窓辺で静かに眺めて過ごす時間'
    text = '\n\t以前は' + separator + '僕が大切にしていたのは、' + target + 'です。\r\n今は、僕はその時間が好きです。' + TAIL
    expected = '以前は、僕は' + target + 'を大切にしていた。今は、僕はその時間が好きです。' + TAIL
    out = assert_body(text, expected)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target


@pytest.mark.parametrize('text', (
    '以前は、彼が望んでいたのは、' + TIME + 'です。',
    '以前は、望んでいたのは、' + TIME + 'です。',
    '以前は私が望んでいたのは、' + TIME + 'です。',
    '今後は、私が大切にしたいのは、' + TIME + 'です。',
    '以前は、今は、私が望んでいたのは、' + TIME + 'です。',
    '以前は、私が望んでいたのは、その時間です。',
    '以前は、私が望んでいたかもしれないのは、' + TIME + 'です。',
    '以前は、私が望んでいましたのは、' + TIME + 'です。',
    '以前は、私が望んでいたのは、' + TIME + 'でした。',
    '以前は、私が振り返ったのは、' + TIME + 'です。',
    '予定が空くなら、今は、私が望んでいるのは、' + TIME + 'です。',
    '以前は、私が望んでいたのは、' + TIME + 'ですと聞いた。',
))
def test_time_does_not_license_missing_author_or_another_unproved_construction(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_competing_objects_are_not_resolved_by_the_latest_time():
    text = ('以前は、私が望んでいたのは、' + TIME + 'です。'
            '今は、私が選びたいのは、一人で静かに手帳を読み返す時間です。'
            '当時は、私が大切にしていたのは、その時間です。' + TAIL)
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.reason_codes == ('unresolved_reference',)


@pytest.mark.parametrize('change', ('relation', 'marker', 'span', 'removed', 'declaration'))
def test_forged_time_or_plan_cannot_drop_a_qualifier(change):
    text = '当時は、私が望んでいなかったのは、' + TIME + 'です。' + TAIL
    out = assert_body(text, '当時は、私は' + TIME + 'を望んでいなかった。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    scope, = meaning.expression_scopes
    if change == 'declaration':
        plan = replace(plan, declaration_eligible=True)
    else:
        altered = (() if change == 'removed' else
            (replace(scope, **({'relation': 'SOURCE_EXPLICIT_REASON'} if change == 'relation' else
                               {'marker': 'も'} if change == 'marker' else
                               {'scope_scalar_span': (1, scope.scope_scalar_span[1])})),))
        meaning = replace(meaning, expression_scopes=altered)
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


def test_public_role_stays_inside_the_same_time_and_complete_object():
    target = '私の友人の秋山さんと落ち着いて言葉を交わす時間'
    text = '当時も、私が望んでいなかったのは、' + target + 'です。今は、私はその時間が好きです。' + TAIL
    expected = '当時も、私は私の友人と落ち着いて言葉を交わす時間を望んでいなかった。今は、私はその時間が好きです。' + TAIL
    out = assert_body(text, expected)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_actual_time_scoped_canonical_body_reaches_the_existing_measured_layout(ratio):
    text = '以前は、私が望んでいなかったのは、' + TIME + 'です。今は、私はその時間が好きです。' + TAIL
    out = assert_body(text, '以前は、私は' + TIME + 'を望んでいなかった。今は、私はその時間が好きです。' + TAIL)
    candidate = out.artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-temporal-focal-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert not layout['native_device_verified']


def test_short_source_keeps_the_existing_content_envelope():
    out = outcome('今は、私が望んでいるのは、本を読むことです。', tier='premium')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_not_eligible',)
