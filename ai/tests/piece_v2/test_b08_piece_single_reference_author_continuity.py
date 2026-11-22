"""Single-reference author continuity in the existing disabled Piece writer.

Synthetic inputs only. This is a surface edit after source/plan validation;
source admission, reference resolution, authorship and product gates stay put.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TARGET = '休日に台所で豆をゆっくり挽く時間'
TAIL = 'まだ、次の休みに試せるかどうかは決めていません。'


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'single-reference-author', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'single-reference-author', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))
    return source, out


def assert_body(text, expected, **options):
    source, out = outcome(text, **options)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for group in plan.block_node_ids for n in group) == tuple(
        node.node_id for node in meaning.graph.nodes)
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end] == node.value.encode('utf-8')
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, **options)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('opening,realized', (
    ('私は' + TARGET + 'を大切にしています。', '私は、' + TARGET + 'を大切にしています。'),
    ('私が大切にしたいのは、' + TARGET + 'です。', '私は、' + TARGET + 'を大切にしたい。'),
    ('私にとって' + TARGET + 'が大切です。', '私にとって、' + TARGET + 'が大切です。'),
))
@pytest.mark.parametrize('predicate', (
    '望んでいる', '望んでいません', '大切にしたいです', '大切にしたくない',
    '望んでいました', '大切にしたくなかった', '望んでいたかもしれない', '選びたいとは限りません',
))
def test_bound_single_direct_argument_can_share_its_explicit_author(opening, realized, predicate):
    second = 'その時間を' + predicate + '。'
    out = assert_body(opening + '私は' + second + TAIL, realized + second + TAIL)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_literal_author_and_determiner_are_not_replaced(speaker, determiner):
    first = speaker + 'は' + TARGET + 'を大切にしています。'
    rest = determiner + '時間を望んでいました。' + TAIL
    assert_body(first + speaker + 'は' + rest,
                speaker + 'は、' + TARGET + 'を大切にしています。' + rest)


@pytest.mark.parametrize('clauses', (
    ('その時間を望んでいました。', 'この時間を大切にしたくなかった。'),
    ('その時間が好きでした。', 'この時間を望んでいたかもしれない。'),
    ('その時間を望んでいます。', 'この時間が苦手ではありません。'),
    ('その時間を望んでいます。', 'この時間を選びたくない。', 'その時間が好きかもしれません。'),
))
def test_one_validated_referent_chain_keeps_distinct_predicates(clauses):
    first = '私が大切にしたいのは、' + TARGET + 'です。'
    out = assert_body(first + ''.join('私は' + clause for clause in clauses) + TAIL,
                      '私は、' + TARGET + 'を大切にしたい。' + ''.join(clauses) + TAIL)
    assert {ref.antecedent_node_id for ref in out.source_meaning.nominal_references} == {'piece:s1'}


@pytest.mark.parametrize('gap', ('\n', '\r\n', '\n\n'))
def test_source_line_breaks_do_not_infer_a_continuation(gap):
    first = '私は' + TARGET + 'を大切にしています。'
    assert_body(first + gap + '私はその時間を望んでいます。' + TAIL,
                '私は、' + TARGET + 'を大切にしています。私は、その時間を望んでいます。' + TAIL)


@pytest.mark.parametrize('middle', ('今日は空が明るかった。', '友人は別の予定を立てていた。'))
def test_intervening_context_does_not_share_a_subject(middle):
    first = '私は' + TARGET + 'を大切にしています。'
    assert_body(first + middle + '私はその時間を望んでいます。' + TAIL,
                '私は、' + TARGET + 'を大切にしています。' + middle + '私は、その時間を望んでいます。' + TAIL)


@pytest.mark.parametrize('target', ('友人が静かに過ごす時間', '友人も静かに過ごす時間', '今は静かに過ごす時間'))
def test_competing_participant_or_contrast_declines_only_the_edit(target):
    assert_body('私は' + target + 'を大切にしています。私はその時間を望んでいます。' + TAIL,
                '私は、' + target + 'を大切にしています。私は、その時間を望んでいます。' + TAIL)


@pytest.mark.parametrize('second,expected', (
    ('僕はその時間を望んでいます。', '僕は、その時間を望んでいます。'),
    ('私が望んでいるのは、その時間です。', '私は、その時間を望んでいる。'),
    ('今は、私はその時間を望んでいます。', '今は、私はその時間を望んでいます。'),
    ('私にとってその時間が必要です。', '私にとって、その時間が必要です。'),
))
def test_another_author_focus_scope_or_viewpoint_is_not_omitted(second, expected):
    assert_body('私は' + TARGET + 'を大切にしています。' + second + TAIL,
                '私は、' + TARGET + 'を大切にしています。' + expected + TAIL)


def test_a_scoped_antecedent_is_not_unconditional_author_evidence():
    first = '無理なく続けられるなら、私は' + TARGET + 'を大切にしたいです。'
    assert_body(first + '私はその時間を望んでいます。' + TAIL,
                first + '私は、その時間を望んでいます。' + TAIL)


def test_a_declined_duplicate_does_not_restart_the_chain():
    first = '私は' + TARGET + 'を大切にしています。'
    assert_body(first + '私はその時間を望んでいる。私はその時間を望んでいる。私はこの時間を選びたくない。' + TAIL,
                '私は、' + TARGET + 'を大切にしています。その時間を望んでいる。私は、その時間を望んでいる。'
                + '私は、この時間を選びたくない。' + TAIL)


def test_public_role_and_unicode_source_offsets_survive_the_edit():
    target = '私の友人の秋山さんと🌱を窓辺で眺める時間'
    out = assert_body('🌱を見た。\r\n\u3000私は' + target + 'を大切にしています。\t私はその時間を望んでいます。' + TAIL,
                      '🌱を見た。\n\n私は、私の友人と🌱を窓辺で眺める時間を大切にしています。'
                      + 'その時間を望んでいます。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert out.source_meaning.envelope.raw_utf8[slice(*ref.antecedent_utf8_span)] == target.encode('utf-8')


@pytest.mark.parametrize('target,head', (('机で小さな紙を折ること', 'こと'), ('長く手元で使ってきたもの', 'もの')))
def test_complete_non_time_nominal_heads_are_preserved(target, head):
    assert_body('私は' + target + 'を大切にしています。私はその' + head + 'を望んでいます。' + TAIL,
                '私は、' + target + 'を大切にしています。その' + head + 'を望んでいます。' + TAIL)


def test_no_padding_or_reduced_minimum_when_optional_edit_would_be_too_short():
    assert_body('私は読むことを選びたい。私はそのことを選びたい。',
                '私は、読むことを選びたい。私は、そのことを選びたい。')


@pytest.mark.parametrize('text', (
    '私はその時間を望んでいます。' + TAIL,
    '私は' + TARGET + 'を大切にしています。その時間を望んでいます。' + TAIL,
))
def test_optional_edit_does_not_invent_missing_reference_or_author(text):
    _, out = outcome(text)
    # A context sentence may be kept verbatim, but never acquire a new author operation.
    if out.artifact is not None:
        assert out.artifact_plan.duties[-2].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
        assert 'その時間を望んでいます。' in out.artifact.piece_text
    else:
        assert out.status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('slot', ('reference_scalar_span', 'reference_utf8_span', 'antecedent_scalar_span', 'antecedent_utf8_span'))
def test_tampered_reference_is_rejected_before_any_optional_edit(slot):
    _, out = outcome('私は' + TARGET + 'を大切にしています。私はその時間を望んでいます。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    ref, = meaning.nominal_references
    a, b = getattr(ref, slot)
    changed = replace(ref, **{slot: (a + 1, b)})
    with pytest.raises(ValueError):
        realize_piece_artifact(replace(meaning, nominal_references=(changed,)), plan,
                               tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_complete_candidate_reaches_existing_measured_layout(ratio):
    out = assert_body('私は' + TARGET + 'を大切にしています。私はその時間を望んでいます。' + TAIL,
                      '私は、' + TARGET + 'を大切にしています。その時間を望んでいます。' + TAIL)
    class Metrics:
        profile_id = 'synthetic-single-reference-author-not-native'
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


@pytest.mark.parametrize('tier,requested_format', (('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay')))
def test_existing_plan_and_format_selection_are_unchanged(tier, requested_format):
    assert_body('私は' + TARGET + 'を大切にしています。私はその時間を望んでいます。' + TAIL,
                '私は、' + TARGET + 'を大切にしています。その時間を望んでいます。' + TAIL,
                tier=tier, requested_format=requested_format)
