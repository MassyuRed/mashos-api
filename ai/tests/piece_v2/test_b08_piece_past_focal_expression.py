"""Retain source-written retrospective focal predicates without a present vow.

Literal synthetic expectations are independent of the production inflection
builder. Exercise the existing CMEE/B8 path, reference resolver and B9 layout;
no new vocabulary, source type, acceptance threshold or public route is added.
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
PAST = ('大切にしたかった', '大切にしていた', '大切にしたくなかった',
        '望んでいた', '望んでいなかった', '選びたかった', '選びたくなかった')


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'past-focal', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'past-focal', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode()
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for block in plan.block_node_ids for n in block) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    for ref in meaning.nominal_references:
        for scalars, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                              (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalars)].encode() == text.encode()[slice(*utf8)]
    for scope in meaning.expression_scopes:
        for scalars, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                              (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalars)].encode() == text.encode()[slice(*utf8)]
    frozen = asdict(meaning), asdict(plan)
    assert realize_piece_artifact(meaning, plan, tier=tier,
                                 requested_format=requested_format) == out.artifact
    assert frozen == (asdict(meaning), asdict(plan))
    source = PieceSourceSnapshot('synthetic-owner', 'past-focal', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert candidate['production_enabled'] is False
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert not plan.declaration_eligible
    assert 'declaration' not in candidate['eligible_formats']
    return out


@pytest.mark.parametrize('predicate', PAST)
@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_plain_past_focal_is_the_same_written_predicate_not_a_present_declaration(predicate, tier):
    source = '私が' + predicate + 'のは、' + TIME + 'です。'
    out = assert_body(source, '私は、' + TIME + 'を' + predicate + '。', tier=tier)
    assert out.artifact.eligible_formats == ('short_essay', 'quote')
    assert out.artifact.format_type == ('short_essay' if tier == 'free' else 'quote')
    assert out.artifact_plan.duties[0].operation == 'SOURCE_FOCAL_TO_FIRST_PERSON'
    refused = outcome(source, tier='premium', requested_format='declaration')
    assert refused.status == EngineStatus.UNAVAILABLE
    assert refused.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('predicate', PAST)
def test_past_focal_pair_keeps_both_references_and_current_reservation(predicate):
    intro = '私が望んでいなかったのは、' + TIME + 'です。私が選びたいのは、' + ACT + 'です。'
    source = intro + '私が' + predicate + 'のは、その時間とこのことです。' + TAIL
    expected = ('私は、' + TIME + 'を望んでいなかった。' + ACT
                + 'を選びたい。その時間とこのことを' + predicate + '。' + TAIL)
    out = assert_body(source, expected)
    assert len(out.source_meaning.nominal_references) == 2
    assert [r.antecedent_node_id for r in out.source_meaning.nominal_references] == ['piece:s1', 'piece:s2']


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_past_focal_antecedent_keeps_exact_author_before_a_current_preference(speaker):
    source = speaker + 'が選びたくなかったのは、' + TIME + 'だ。' + speaker + 'はその時間が好きです。' + TAIL
    out = assert_body(source, speaker + 'は、' + TIME + 'を選びたくなかった。その時間が好きです。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert source[slice(*ref.antecedent_scalar_span)] == TIME


@pytest.mark.parametrize('marker', ('ので', 'なら', 'けれど'))
def test_written_outer_scope_does_not_erase_inner_past_negation(marker):
    source = '静かに過ごせる' + marker + '、私が望んでいなかったのは、' + TIME + 'です。' + TAIL
    out = assert_body(source, '静かに過ごせる' + marker + '、私は' + TIME + 'を望んでいなかった。' + TAIL)
    assert len(out.source_meaning.expression_scopes) == 1


@pytest.mark.parametrize('gap', ('\n', '\r\n'))
def test_source_line_break_keeps_a_later_explicit_self_topic(gap):
    source = '私が大切にしていたのは、' + TIME + 'です。' + gap + '私はその時間が好きです。' + TAIL
    assert_body(source, '私は、' + TIME + 'を大切にしていた。私は、その時間が好きです。' + TAIL)


@pytest.mark.parametrize('expression', (
    '大切にしたかったのは、その時間です。',
    '彼が大切にしたかったのは、その時間です。',
    '私が大切にしたかったのは、その時間とこの時間です。',
    '私が大切にしたかったのは、その時間とあのことです。',
    '私が大切にしたかったのは、その時間とこのものです。',
    '私が大切にしたかったのは、その時間とこのこととその時間です。',
    '私が大切にしたかったのは、その時間よりこのことです。',
    '私が大切にしたかったのは、その時間かこのことです。',
    '私が振り返ったのは、その時間です。',
    '私が望んでいましたのは、その時間です。',
    '私が望んでいたかもしれないのは、その時間です。',
    '私が大切にしたかったのは、その時間でした。',
    '以前は、私が大切にしたかったのは、その時間です。',
))
def test_past_surface_does_not_infer_author_other_predicate_or_unresolved_reference(expression):
    intro = '私が選びたいのは、' + TIME + 'です。私が選びたいのは、' + ACT + 'です。'
    out = outcome(intro + expression + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('predicate', PAST)
def test_existing_direct_past_word_order_and_finite_modal_remain_unchanged(predicate):
    assert_body('私は' + TIME + 'を' + predicate + '。', '私は、' + TIME + 'を' + predicate + '。')
    assert_body('私は' + TIME + 'を' + predicate + 'かもしれません。',
                '私は、' + TIME + 'を' + predicate + 'かもしれません。')


def test_plan_cannot_promote_retrospection_or_drop_the_reservation():
    source = '私が選びたかったのは、' + TIME + 'です。'
    out = assert_body(source, '私は、' + TIME + 'を選びたかった。')
    with pytest.raises(ValueError):
        realize_piece_artifact(out.source_meaning,
            replace(out.artifact_plan, declaration_eligible=True), tier='premium', requested_format=None)
    out = outcome(source + TAIL)
    assert out.status == EngineStatus.GENERATED
    with pytest.raises(ValueError):
        realize_piece_artifact(out.source_meaning,
            replace(out.artifact_plan, block_node_ids=(('piece:s1',),)), tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_actual_past_focal_body_reaches_unchanged_measured_layout(ratio):
    source = '私が望んでいなかったのは、' + TIME + 'です。私はその時間が好きです。' + TAIL
    out = assert_body(source, '私は、' + TIME + 'を望んでいなかった。その時間が好きです。' + TAIL)
    candidate = out.artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-past-focal-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(r['text'] for r in layout['lines'] if r['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert not layout['native_device_verified']
