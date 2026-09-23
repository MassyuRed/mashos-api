"""Synthetic paired-reference paragraphs keep meaning while sharing their author."""
from dataclasses import asdict, replace
from copy import deepcopy
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


def outcome(text, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-paired-author', '1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-paired-author', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def generated(text):
    out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-paired-author', '1', text)
    candidate = out.artifact.as_candidate()
    assert generate_piece_candidate(source, authenticated_owner_id=source.owner_id) == candidate
    assert candidate['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.automatic_progression
    return out


def introduction(speaker='僕', first_kind='value', second_kind='focal'):
    def clause(kind, target):
        if kind == 'focal':
            return speaker + 'が大切にしたいのは、' + target + 'です。'
        return speaker + 'にとって' + target + 'が大切です。'
    return clause(first_kind, TIME) + clause(second_kind, ACT)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('operator', ('と', 'より'))
def test_three_explicit_clauses_share_the_proven_author_not_their_evaluations(speaker, operator):
    target = 'その時間' + operator + '、このこと'
    text = introduction(speaker) + speaker + 'は' + target + 'が好きかもしれません。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == (speaker + 'にとって、' + TIME + 'が大切です。'
        + ACT + 'を大切にしたい。' + target + 'が好きかもしれません。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode()
    assert [node.value for node in meaning.graph.nodes] == [
        speaker + 'にとって' + TIME + 'が大切です。',
        speaker + 'が大切にしたいのは、' + ACT + 'です。',
        speaker + 'は' + target + 'が好きかもしれません。', TAIL]
    assert [r.antecedent_node_id for r in meaning.nominal_references] == ['piece:s1', 'piece:s2']
    assert [r.reference_node_id for r in meaning.nominal_references] == ['piece:s3', 'piece:s3']
    for ref, obj in zip(meaning.nominal_references, (TIME, ACT), strict=True):
        assert text[slice(*ref.antecedent_scalar_span)] == obj
        assert text.encode()[slice(*ref.antecedent_utf8_span)].decode() == obj
    frame = meaning.personal_evaluations[-1]
    assert text[slice(*frame.scalar_parts[2])] == target
    assert text.encode()[slice(*frame.utf8_parts[2])].decode() == target
    assert frame.commitment == 'POSSIBLE'
    assert plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3', 'piece:s4'),)
    frozen = deepcopy((asdict(meaning), asdict(plan)))
    assert realize_piece_artifact(meaning, plan, tier='free', requested_format=None) == out.artifact
    assert (asdict(meaning), asdict(plan)) == frozen


@pytest.mark.parametrize('first_kind,second_kind', (('focal', 'focal'), ('value', 'value')))
def test_first_visible_author_and_each_explicit_value_viewpoint_remain(first_kind, second_kind):
    text = introduction('私', first_kind, second_kind) + '私はその時間と、このことが好きです。' + TAIL
    out = generated(text)
    if first_kind == 'focal':
        assert out.artifact.piece_text == ('私は、' + TIME + 'を大切にしたい。'
            + ACT + 'を大切にしたい。その時間と、このことが好きです。' + TAIL)
    else:
        assert out.artifact.piece_text == ('私にとって、' + TIME + 'が大切です。'
            '私にとって、' + ACT + 'が大切です。その時間と、このことが好きです。' + TAIL)


@pytest.mark.parametrize('ending,polarity,time,commitment', (
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではありません', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('とは限りません', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
))
def test_reversed_comparison_retains_complete_predicate_scope_and_source_order(ending, polarity, time, commitment):
    target = 'そのことより、\tこの時間'
    text = introduction('僕') + '僕は' + target + 'が好き' + ending + '。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text.endswith(target + 'が好き' + ending + '。' + TAIL)
    assert out.artifact.piece_text.count('僕') == 1
    frame = out.source_meaning.personal_evaluations[-1]
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert [ref.antecedent_node_id for ref in out.source_meaning.nominal_references] == ['piece:s2', 'piece:s1']


@pytest.mark.parametrize('barrier', ('different_first_author', 'different_second_author',
    'newline_first', 'newline_second', 'time_first', 'time_last', 'condition_last',
    'intervening_context', 'competing_subject', 'explicit_value_viewpoint', 'focal_preference'))
def test_uncertain_author_or_scope_boundaries_keep_the_written_topic(barrier):
    first = '僕にとって' + TIME + 'が大切です。'
    second = '僕が大切にしたいのは、' + ACT + 'です。'
    last = '僕はその時間と、このことが好きです。'
    if barrier == 'different_first_author': first = first.replace('僕', '私')
    elif barrier == 'different_second_author': second = second.replace('僕', '私')
    elif barrier == 'newline_first': first += '\r\n'
    elif barrier == 'newline_second': second += '\n'
    elif barrier == 'time_first': first = '以前は、' + first
    elif barrier == 'time_last': last = '今は、' + last
    elif barrier == 'condition_last': last = '日程が合うなら、' + last
    elif barrier == 'intervening_context': second += '友人は別の日に出かけた。'
    elif barrier == 'competing_subject': first = first.replace(TIME, '友人が海を眺める時間')
    elif barrier == 'explicit_value_viewpoint': last = '僕にとってその時間と、このことが必要です。'
    elif barrier == 'focal_preference': last = '僕が好きなのは、その時間と、このことです。'
    text = first + second + last + TAIL
    out = generated(text)
    body = out.artifact.piece_text
    assert ('僕は、その時間と、このことが好きです。' in body
            or '僕はその時間と、このことが好きです。' in body
            or '僕にとって、その時間と、このことが必要です。' in body)
    assert ('僕は、' + ACT + 'を大切にしたい。' in body
            or '私は、' + ACT + 'を大切にしたい。' in body)


def test_names_are_publicized_but_neither_relationship_is_erased():
    text = ('僕にとって同僚の西さんと展示を見る時間が大切です。'
        '僕が選びたいのは、先生の北さんへ感想を伝えることです。'
        '僕はその時間と、このことが苦手ではありません。まだ、参加する日は決めていません。')
    out = generated(text)
    assert out.artifact.piece_text == ('僕にとって、同僚と展示を見る時間が大切です。'
        '先生へ感想を伝えることを選びたい。その時間と、このことが苦手ではありません。'
        'まだ、参加する日は決めていません。')
    assert len(out.source_meaning.role_bindings) == 2
    assert all(name not in out.artifact.piece_text for name in ('西さん', '北さん'))


@pytest.mark.parametrize('change', ('reference', 'author', 'scope', 'plan'))
def test_source_and_plan_validation_precede_the_optional_edit(change):
    text = introduction() + '僕はその時間と、このことが好きです。' + TAIL
    out = generated(text)
    meaning, plan = out.source_meaning, out.artifact_plan
    if change == 'reference':
        refs = meaning.nominal_references
        meaning = replace(meaning, nominal_references=(replace(refs[0], antecedent_node_id='piece:s2'), refs[1]))
    elif change == 'author':
        frames = meaning.personal_evaluations
        meaning = replace(meaning, personal_evaluations=(replace(frames[0], scalar_parts=((0, 0), *frames[0].scalar_parts[1:])), *frames[1:]))
    elif change == 'scope':
        nodes = meaning.graph.nodes
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(replace(nodes[0], value='今は、' + nodes[0].value), *nodes[1:])))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1', 'piece:s2'), ('piece:s3', 'piece:s4')))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_short_essay_enters_existing_layout_without_side_effects(tier, ratio):
    text = introduction() + '僕はその時間と、このことが好きかもしれません。' + TAIL
    out = outcome(text, tier=tier)
    assert out.status == EngineStatus.GENERATED
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    class Metrics:
        profile_id = 'synthetic-paired-author-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, size):
            a = len(text) * size
            return TextMeasurement(a, 0, -.8 * size, a, .2 * size)
    before = deepcopy((candidate, recipe))
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(candidate['content_payload']['body_blocks']))] == candidate['content_payload']['body_blocks']
    assert layout['layout_state'] == 'fit' and not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert outcome(text, tier='premium', requested_format='declaration').status == EngineStatus.UNAVAILABLE
