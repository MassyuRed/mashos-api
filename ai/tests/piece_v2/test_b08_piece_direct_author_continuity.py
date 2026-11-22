"""A direct expression can establish the author of its bound preference.

Synthetic inputs only. No new input admission or inferred speaker; the
existing optional writer edit keeps source/plan identities and every claim.
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
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

TARGET = '一人で静かに手帳を開く時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
PREDICATES = (
    '大切にしたい', '大切にしている', '大切にしたくない',
    '望んでいる', '望んでいない', '選びたい', '選びたくない',
    '大切にしたいです', '大切にしています', '大切にしたくないです',
    '望んでいます', '望んでいません', '選びたいです', '選びたくないです',
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'direct-author', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'direct-author', source, source.owner_id, source.saved_input_id, source.source_version))
    return source, out


def assert_body(text, expected):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for group in plan.block_node_ids for n in group) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode('utf-8')[ev.utf8_start:ev.utf8_end] == node.value.encode('utf-8')
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                            (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    return out


@pytest.mark.parametrize('predicate', PREDICATES)
def test_direct_author_is_shared_without_changing_either_predicate(predicate):
    opening = f'私は{TARGET}を{predicate}。'
    ending = 'その時間が好きではなかったかもしれません。'
    out = assert_body(opening + '私は' + ending + TAIL,
                      f'私は、{TARGET}を{predicate}。' + ending + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (
        'NEGATIVE', 'PAST', 'POSSIBLE')
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_only_the_repeated_literal_author_is_omitted(speaker, determiner):
    first = f'{speaker}は{TARGET}を大切にしています。'
    second = determiner + '時間が好きです。'
    assert_body(first + speaker + 'は' + second + TAIL,
                f'{speaker}は、{TARGET}を大切にしています。' + second + TAIL)


@pytest.mark.parametrize('target,head', (
    ('机で小さな紙を折ること', 'こと'),
    ('手元で長く使ってきたもの', 'もの'),
    ('🌱を窓辺で眺める時間', '時間'),
))
def test_full_nominal_argument_and_following_chain_are_preserved(target, head):
    clauses = [f'その{head}が好きです。', f'この{head}が苦手ではありません。']
    out = assert_body(f'僕は{target}を大切にしています。' + ''.join('僕は' + c for c in clauses) + TAIL,
                      f'僕は、{target}を大切にしています。' + ''.join(clauses) + TAIL)
    assert {ref.antecedent_node_id for ref in out.source_meaning.nominal_references} == {'piece:s1'}


@pytest.mark.parametrize('gap', ('\n', '\r\n', '\n\n'))
def test_source_line_boundaries_keep_the_explicit_topic(gap):
    first = f'僕は{TARGET}を大切にしています。'
    rest = '僕はその時間が好きです。' + TAIL
    assert_body(first + gap + rest,
                f'僕は、{TARGET}を大切にしています。僕は、その時間が好きです。' + TAIL)


@pytest.mark.parametrize('second,expected', (
    ('僕はその時間が好きです。', '僕は、その時間が好きです。'),
    ('私にとってその時間が大切です。', '私にとって、その時間が大切です。'),
    ('私が好きなのは、その時間です。', '私は、その時間が好きです。'),
    ('私はその時間より、川辺でゆっくり歩くことが好きです。',
     '私は、その時間より、川辺でゆっくり歩くことが好きです。'),
    ('私はまだ迷っているけれど、私はその時間が好きです。',
     '私はまだ迷っているけれど、その時間が好きです。'),
))
def test_distinct_authors_viewpoints_focus_and_scopes_keep_their_boundaries(second, expected):
    assert_body(f'私は{TARGET}を大切にしています。' + second + TAIL,
                f'私は、{TARGET}を大切にしています。' + expected + TAIL)


@pytest.mark.parametrize('middle', ('今日は空が明るかった。', '友人は別の予定を立てていた。'))
def test_intervening_context_does_not_establish_author_continuity(middle):
    assert_body(f'私は{TARGET}を大切にしています。' + middle + '私はその時間が好きです。' + TAIL,
                f'私は、{TARGET}を大切にしています。' + middle + '私は、その時間が好きです。' + TAIL)


@pytest.mark.parametrize('target,expected_status', (
    ('友人が静かに話す時間', EngineStatus.GENERATED),
    ('私は一人で過ごす時間', EngineStatus.UNAVAILABLE),
    ('友人も静かに過ごす時間', EngineStatus.GENERATED),
))
def test_competing_participant_or_topic_in_the_argument_declines_only_the_edit(target, expected_status):
    # An unsupported source remains unsupported; this edit never grants input admission.
    text = f'私は{target}を大切にしています。私はその時間が好きです。' + TAIL
    _, out = outcome(text)
    assert out.status == expected_status
    if expected_status == EngineStatus.GENERATED:
        assert out.artifact.piece_text == f'私は、{target}を大切にしています。私は、その時間が好きです。' + TAIL
    else:
        assert out.artifact is None


def test_scoped_direct_antecedent_is_not_treated_as_unconditional():
    first = f'無理なく続けられるなら、私は{TARGET}を大切にしたいです。'
    assert_body(first + '私はその時間が好きです。' + TAIL,
                first + '私は、その時間が好きです。' + TAIL)


def test_continuation_cannot_restart_after_a_declined_duplicate():
    first = f'私は{TARGET}を大切にしています。'
    assert_body(first + '私はその時間が好き。私はその時間が好き。私はこの時間が苦手ではない。' + TAIL,
                f'私は、{TARGET}を大切にしています。その時間が好き。私は、その時間が好き。'
                + '私は、この時間が苦手ではない。' + TAIL)


def test_a_public_role_and_its_original_source_coordinates_survive_the_edit():
    target = '私の友人の秋山さんと落ち着いて話す時間'
    out = assert_body('🌱を見た。\r\n\u3000' + f'私は{target}を大切にしています。\t私はその時間が好きです。' + TAIL,
                      '🌱を見た。\n\n私は、私の友人と落ち着いて話す時間を大切にしています。その時間が好きです。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert out.source_meaning.envelope.raw_utf8[slice(*ref.antecedent_utf8_span)] == target.encode()


def test_below_minimum_optional_edit_is_declined_without_padding():
    text = '私は読むことを選びたい。私はそのことが好き。'
    assert_body(text, '私は、読むことを選びたい。私は、そのことが好き。')


@pytest.mark.parametrize('mutation', ('reference', 'speaker', 'duty'))
def test_forged_source_or_plan_cannot_authorize_topic_omission(mutation):
    _, out = outcome(f'私は{TARGET}を大切にしています。私はその時間が好きです。' + TAIL)
    assert out.status == EngineStatus.GENERATED
    meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'reference':
        ref, = meaning.nominal_references
        meaning = replace(meaning, nominal_references=(replace(ref, antecedent_scalar_span=(0, 2)),))
    elif mutation == 'speaker':
        frame, = meaning.personal_evaluations
        meaning = replace(meaning, personal_evaluations=(replace(frame, scalar_parts=((0, 2), *frame.scalar_parts[1:])),))
    else:
        plan = replace(plan, duties=(replace(plan.duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT'), *plan.duties[1:]))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


class Metrics:
    profile_id = 'direct-author-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_complete_edited_body_is_the_input_of_the_existing_layout(ratio):
    out = assert_body(f'私は{TARGET}を大切にしています。私はその時間が好きです。' + TAIL,
                      f'私は、{TARGET}を大切にしています。その時間が好きです。' + TAIL)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
