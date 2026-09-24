"""Synthetic direct two-object paragraphs retain every source proposition.

Only an already-admitted, source-bound author's repeated topic is optional.
No new predicate, reference, input admission or public/runtime capability.
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

TIME = '森で静かに風の音を聞く時間'
ACT = '自分の考えをノートに書くこと'
TAIL = 'まだ、毎日続けるかは決めていません。'
PREDICATES = (
    '大切にしたい', '大切にしている', '大切にしたくない',
    '望んでいる', '望んでいない', '選びたい', '選びたくない',
    '大切にしたいです', '大切にしています', '大切にしたくないです',
    '望んでいます', '望んでいません', '選びたいです', '選びたくないです',
)


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'paired-direct-author', '1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'paired-direct-author', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_body(text, expected):
    out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
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
    frozen = asdict(meaning), asdict(plan)
    source = PieceSourceSnapshot('synthetic-owner', 'paired-direct-author', '1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert realize_piece_artifact(meaning, plan, tier='free', requested_format=None) == out.artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.artifact.piece_text == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    return out


def direct(target, predicate, speaker='私'):
    return speaker + 'は' + target + 'を' + predicate + '。'


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('operator', ('と', 'より'))
def test_direct_pair_and_preference_share_only_the_same_literal_author(speaker, operator):
    target = 'その時間' + operator + '、このこと'
    ending = target + 'が好きかもしれません。'
    text = direct(TIME, '大切にしています', speaker) + direct(ACT, '選びたいです', speaker)
    out = assert_body(text + speaker + 'は' + ending + TAIL,
        speaker + 'は、' + TIME + 'を大切にしています。' + ACT + 'を選びたいです。' + ending + TAIL)
    assert [r.antecedent_node_id for r in out.source_meaning.nominal_references] == ['piece:s1', 'piece:s2']


@pytest.mark.parametrize('predicate', PREDICATES)
@pytest.mark.parametrize('position', (0, 1))
def test_both_complete_direct_predicates_keep_their_own_register_and_polarity(predicate, position):
    predicates = ['大切にしています', '望んでいません']
    predicates[position] = predicate
    first, second = (direct(target, pred) for target, pred in zip((TIME, ACT), predicates, strict=True))
    ending = 'そのことより、この時間が好きではなかったかもしれません。'
    out = assert_body(first + second + '私は' + ending + TAIL,
        first.replace('私は', '私は、', 1) + second.removeprefix('私は') + ending + TAIL)
    frame = out.source_meaning.personal_evaluations[-1]
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')
    assert [r.antecedent_node_id for r in out.source_meaning.nominal_references] == ['piece:s2', 'piece:s1']


@pytest.mark.parametrize('first_kind,second_kind', (
    ('direct', 'value'), ('value', 'direct'), ('direct', 'focal'), ('focal', 'direct'),
))
def test_existing_focal_and_value_antecedents_share_the_same_direct_pair(first_kind, second_kind):
    def clause(kind, target):
        if kind == 'direct': return direct(target, '大切にしています'), '私は、' + target + 'を大切にしています。'
        if kind == 'value': return '私にとって' + target + 'が大切です。', '私にとって、' + target + 'が大切です。'
        return '私が選びたいのは、' + target + 'です。', '私は、' + target + 'を選びたい。'
    first, a = clause(first_kind, TIME)
    second, b = clause(second_kind, ACT)
    if second_kind != 'value': b = b.removeprefix('私は、')
    end = 'その時間とこのことが苦手ではありません。'
    assert_body(first + second + '私は' + end + TAIL, a + b + end + TAIL)


@pytest.mark.parametrize('barrier', (
    'first_author', 'second_author', 'last_author', 'first_newline', 'second_newline',
    'first_scope', 'second_scope', 'last_scope', 'intervening', 'participant',
    'viewpoint', 'focal_preference', 'literal_operand',
))
def test_unproven_pair_keeps_explicit_topics_without_rejecting_admitted_input(barrier):
    first = direct(TIME, '大切にしています')
    second = direct(ACT, '望んでいません')
    last = '私はその時間と、このことが好きです。'
    if barrier == 'first_author': first = first.replace('私', '僕')
    elif barrier == 'second_author': second = second.replace('私', '僕')
    elif barrier == 'last_author': last = last.replace('私', '僕')
    elif barrier == 'first_newline': first += '\r\n'
    elif barrier == 'second_newline': second += '\n'
    elif barrier == 'first_scope': first = '無理なく続けられるなら、' + first
    elif barrier == 'second_scope': second = '日程が合うなら、' + second
    elif barrier == 'last_scope': last = '今は、' + last
    elif barrier == 'intervening': second += '友人は別の日に出かけた。'
    elif barrier == 'participant': first = first.replace(TIME, '友人が海を眺める時間')
    elif barrier == 'viewpoint': last = '私にとってその時間と、このことが必要です。'
    elif barrier == 'focal_preference': last = '私が好きなのは、その時間と、このことです。'
    elif barrier == 'literal_operand': last = '私はその時間より、川辺で一人で歩くことが好きです。'
    text = first + second + last + TAIL
    out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    body = out.artifact.piece_text
    assert ('私は、' + ACT + 'を望んでいません。' in body
            or '私は' + ACT + 'を望んでいません。' in body
            or '僕は、' + ACT + 'を望んでいません。' in body)
    assert (('私は、その' in body) or ('僕は、その' in body)
            or '今は、私はその' in body or '私にとって、その' in body)
    assert body.endswith(TAIL)


@pytest.mark.parametrize('opening', ('🌱を見た。\r\n\u3000', '静かな朝だった。\t'))
def test_original_unicode_coordinates_and_both_public_roles_remain(opening):
    time = '同僚の西さんと展示を見る時間'
    act = '先生の北さんへ感想を伝えること'
    text = opening + direct(time, '大切にしています') + '\t' + direct(act, '選びたいです')
    ending = 'その時間より\tこのことが好きです。'
    out = assert_body(text + '私は' + ending + TAIL,
        opening.strip() + '\n\n私は、同僚と展示を見る時間を大切にしています。'
        '先生へ感想を伝えることを選びたいです。' + ending + TAIL)
    assert len(out.source_meaning.role_bindings) == 2
    assert all(name not in out.artifact.piece_text for name in ('西さん', '北さん'))


@pytest.mark.parametrize('text', (
    '私は読むことを選びたい。私は書くことを選びたい。私はそのことと、このことが好きです。',
    '私はその時間を大切にしています。私は書くことを選びたい。私はその時間と、このことが好きです。',
))
def test_missing_or_ambiguous_referents_gain_no_new_input_admission(text):
    out = outcome(text + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('mutation', ('scalar', 'utf8', 'node', 'plan'))
def test_forged_pair_cannot_authorize_the_editorial_change(mutation):
    text = direct(TIME, '大切にしています') + direct(ACT, '選びたいです') + '私はその時間と、このことが好きです。' + TAIL
    out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    meaning, plan = out.source_meaning, out.artifact_plan
    refs = meaning.nominal_references
    if mutation in ('scalar', 'utf8'):
        field = 'antecedent_' + mutation + '_span'
        meaning = replace(meaning, nominal_references=(replace(refs[0], **{field: (0, 2)}), refs[1]))
    elif mutation == 'node':
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(
            replace(meaning.graph.nodes[0], value=meaning.graph.nodes[0].value.replace('私', '僕')),
            *meaning.graph.nodes[1:])))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1',), ('piece:s2', 'piece:s3', 'piece:s4')))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_canonical_edited_body_enters_the_existing_image_layout(ratio):
    text = direct(TIME, '大切にしています') + direct(ACT, '選びたいです') + '私はその時間と、このことが好きです。' + TAIL
    out = assert_body(text, '私は、' + TIME + 'を大切にしています。' + ACT + 'を選びたいです。'
                      'その時間と、このことが好きです。' + TAIL)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    class Metrics:
        profile_id = 'paired-direct-synthetic-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, size):
            width = len(text) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(l['text'] for l in layout['lines'] if l['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']
    assert outcome(text, tier='premium', requested_format='declaration').status == EngineStatus.UNAVAILABLE
