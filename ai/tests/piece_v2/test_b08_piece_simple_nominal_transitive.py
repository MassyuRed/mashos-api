"""Complete simple nominal objects in the existing disabled Piece consumer.

Synthetic inputs only. Reuse the evaluation owner's nominal shape; preserve
transitive arguments, written authors, predicates and all surrounding claims.
This does not extend the reference resolver or the evaluative focus grammar.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import (
    _direct_transitive_expression,
)
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TAIL = 'まだ、週末に予定を入れるかは決めていません。'


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'simple-nominal', 'v1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'simple-nominal', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))
    return source, result


def assert_body(text, expected, **options):
    source, result = outcome(text, **options)
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    assert result.artifact.piece_text == expected
    meaning, plan = result.source_meaning, result.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert plan == compile_piece_artifact_plan(meaning)
    assert tuple(n for block in plan.block_node_ids for n in block) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode()[evidence.utf8_start:evidence.utf8_end] == node.value.encode()
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    frozen = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, **options)
    assert candidate == result.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == frozen
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled'] and not result.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return result


@pytest.mark.parametrize('target', ('散歩', '手芸', 'ハーブティー'))
@pytest.mark.parametrize('predicate', ('大切にしたい', '選びたくない', '望んでいる'))
@pytest.mark.parametrize('focal', (False, True))
def test_complete_object_is_not_padded_with_an_invented_nominalizer(target, predicate, focal):
    first = ('私が' + predicate + 'のは、' + target + 'です。' if focal
             else '私は' + target + 'を' + predicate + '。')
    expected = '私は、' + target + 'を' + predicate + '。' + ('\n\n' if focal else '') + TAIL
    result = assert_body(first + TAIL, expected)
    assert result.source_meaning.nominal_references == ()


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('focal', (False, True))
def test_literal_written_author_is_preserved(speaker, focal):
    first = (speaker + 'が選びたいのは、散歩です。' if focal
             else speaker + 'は散歩を選びたい。')
    assert_body(first + TAIL, speaker + 'は、散歩を選びたい。' + ('\n\n' if focal else '') + TAIL)


@pytest.mark.parametrize('predicate', (
    '大切にしています', '望んでいません', '大切にしたくなかった',
    '望んでいました', '望んでいませんでした', '選びたかった',
    '望んでいたかもしれません', '選びたくないとは限りません',
))
def test_direct_predicate_preserves_register_tense_negation_and_modality(predicate):
    assert_body('私は手芸を' + predicate + '。' + TAIL,
                '私は、手芸を' + predicate + '。' + TAIL)


@pytest.mark.parametrize('predicate', (
    '大切にしたかった', '大切にしたくなかった', '望んでいなかった',
    '望んでいたかもしれない', '選びたくなかったとは限らない',
))
def test_focal_predicate_is_not_promoted_to_a_current_affirmative_wish(predicate):
    assert_body('私が' + predicate + 'のは、手芸です。' + TAIL,
                '私は、手芸を' + predicate + '。\n\n' + TAIL)


@pytest.mark.parametrize('premise', (
    '予定が空くなら', '予定が空くならば', '余裕がなかったので',
    '迷っていたけれど', '以前は', 'これからも',
))
@pytest.mark.parametrize('focal', (False, True))
def test_source_scope_stays_attached_to_the_complete_transitive_expression(premise, focal):
    first = ('私が選びたいのは、手芸です。' if focal else '私は手芸を選びたい。')
    result = assert_body(premise + '、' + first + TAIL,
                         premise + '、私は手芸を選びたい。' + TAIL)
    scope, = result.source_meaning.expression_scopes
    assert result.source_meaning.envelope.raw_utf8[slice(*scope.expression_utf8_span)] == first.encode()


@pytest.mark.parametrize('focal_index', (0, 1, 2))
def test_context_source_order_and_unicode_ranges_are_not_rewritten(focal_index):
    original = ['🌱を眺めた。', TAIL]
    original.insert(focal_index, '僕が大切にしたいのは、手芸です。')
    visible = list(original)
    visible[focal_index] = '僕は、手芸を大切にしたい。'
    assert_body('\r\n\u3000'.join(original), '\n\n'.join(visible))


@pytest.mark.parametrize('sentence', (
    '私は友人の希望を望んでいる。', '私は花と音楽を望んでいる。',
    '私はその手芸を望んでいる。', '私はこれを望んでいる。',
    '私は友人が選ぶ散歩を望んでいる。', '私は散歩なら手芸を望んでいる。',
    '私は散歩を望んでいますかもしれない。', '私は散歩を望んでいると聞いた。',
    '散歩を望んでいる。', '友人は散歩を望んでいる。',
))
def test_other_argument_shapes_authors_and_embedded_predicates_are_not_added(sentence):
    assert _direct_transitive_expression(sentence) is None
    _, result = outcome(sentence + TAIL)
    assert result.status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('later', ('私はその時間が好きです。', '私はそのことを選びたい。'))
def test_a_simple_nominal_does_not_invent_a_time_or_event_antecedent(later):
    _, result = outcome('私は手芸を大切にしています。' + later + TAIL)
    assert result.status == EngineStatus.UNAVAILABLE


def test_existing_evaluation_keeps_its_separate_viewpoint_and_focus_boundary():
    assert_body('私にとって散歩が大切です。' + TAIL,
                '私にとって、散歩が大切です。' + TAIL)
    _, result = outcome('私が好きなのは、友人です。' + TAIL)
    assert result.status == EngineStatus.UNAVAILABLE


def test_independent_authors_do_not_become_one_author():
    assert_body('私は手芸を大切にしています。僕は散歩を望んでいません。' + TAIL,
                '私は、手芸を大切にしています。僕は、散歩を望んでいません。' + TAIL)


def test_no_minimum_length_relaxation_or_filler():
    _, result = outcome('私は散歩を望んでいる。')
    assert result.status == EngineStatus.UNAVAILABLE
    assert result.artifact is None


def test_source_plan_tampering_still_fails():
    result = assert_body('私が選びたくないのは、手芸です。' + TAIL,
                         '私は、手芸を選びたくない。\n\n' + TAIL)
    plan = replace(result.artifact_plan, declaration_eligible=True)
    with pytest.raises(ValueError):
        realize_piece_artifact(result.source_meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_canonical_complete_body_reaches_the_unchanged_measured_layout(ratio):
    result = assert_body('予定が空くなら、私が選びたいのは、手芸です。' + TAIL,
                         '予定が空くなら、私は手芸を選びたい。' + TAIL)
    class Metrics:
        profile_id = 'synthetic-simple-nominal-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, size):
            width = len(text) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    candidate = result.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(result.artifact.body_blocks))] == list(result.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']
