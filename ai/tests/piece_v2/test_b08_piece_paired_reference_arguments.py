"""Synthetic two-reference arguments stay source-bound and undivided in Piece."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import itertools

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

OBJECTS = {
    '時間': '川辺でゆっくり歩く時間',
    'こと': '自分の考えを紙に書くこと',
    'もの': '手元で長く使ってきたもの',
}
TAIL = 'まだ、毎日続けるかは決めていません。'


def source_for(text):
    return PieceSourceSnapshot('synthetic-owner', 'synthetic-paired-arguments', 'v1', text)


def run(text, **options):
    source = source_for(text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-paired-arguments', source, source.owner_id,
        source.saved_input_id, source.source_version, **options))


def intro(heads=('時間', 'こと'), speaker='私'):
    return ''.join(speaker + 'にとって' + OBJECTS[head] + 'が大切です。' for head in heads)


def argument(heads, operator, gap='、'):
    return 'その' + heads[0] + operator + gap + 'この' + heads[1]


def generated(text):
    out = run(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    candidate = out.artifact.as_candidate()
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    assert candidate['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    source = source_for(text)
    assert generate_piece_candidate(source, authenticated_owner_id=source.owner_id) == candidate
    assert out.artifact.eligible_formats == ('short_essay',)
    return out


def check_bindings(out, text, heads, target):
    meaning = out.source_meaning
    assert meaning.envelope.raw_utf8 == text.encode()
    refs = meaning.nominal_references
    assert len(refs) == 2
    for index, (ref, head) in enumerate(zip(refs, heads, strict=True)):
        expected = ('その' if index == 0 else 'この') + head
        assert ref.reference_node_id == 'piece:s3'
        assert ref.antecedent_node_id == 'piece:s' + str(index + 1)
        assert text[slice(*ref.antecedent_scalar_span)] == OBJECTS[head]
        assert text.encode()[slice(*ref.antecedent_utf8_span)].decode() == OBJECTS[head]
        assert text[slice(*ref.reference_scalar_span)] == expected
        assert text.encode()[slice(*ref.reference_utf8_span)].decode() == expected
        assert ref.nominal_head == head
    frames = meaning.personal_evaluations
    assert len(frames) == 3  # One joint/comparative evaluation, not one per operand.
    frame = frames[-1]
    assert frame.node_id == 'piece:s3'
    assert text[slice(*frame.scalar_parts[2])] == target
    assert text.encode()[slice(*frame.utf8_parts[2])].decode() == target
    edges = [edge for edge in meaning.graph.edges if edge.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']
    assert [edge.target_node_id for edge in edges] == ['piece:s1', 'piece:s2']
    assert [edge.source_node_id for edge in edges] == ['piece:s3', 'piece:s3']
    assert [edge.evidence_ids for edge in edges] == [('piece:e1', 'piece:e3'), ('piece:e2', 'piece:e3')]
    assert out.artifact_plan.block_node_ids == (tuple(node.node_id for node in meaning.graph.nodes),)


@pytest.mark.parametrize('heads', tuple(itertools.combinations(OBJECTS, 2)))
@pytest.mark.parametrize('operator', ('より', 'と'))
@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕'))
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_two_prior_objects_form_one_complete_evaluation_argument(heads, operator, speaker, order):
    target = argument(heads, operator)
    last = (speaker + 'は' + target + 'が好きです。' if order == 'finite'
            else speaker + 'が好きなのは、' + target + 'です。')
    text = intro(heads, speaker) + last + TAIL
    out = generated(text)
    expected = ''.join(speaker + 'にとって、' + OBJECTS[h] + 'が大切です。' for h in heads)
    assert out.artifact.piece_text == expected + speaker + 'は、' + target + 'が好きです。' + TAIL
    check_bindings(out, text, heads, target)


@pytest.mark.parametrize('operator', ('より', 'と'))
@pytest.mark.parametrize('ending,polarity,time,commitment', (
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではありません', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('ではありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('かもしれません', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('とは限りません', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
))
def test_whole_argument_keeps_negation_tense_and_commitment(operator, ending, polarity, time, commitment):
    heads = ('こと', '時間')
    target = argument(heads, operator)
    text = intro(heads) + '私にとって' + target + 'が必要' + ending + '。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text.endswith('私にとって、' + target + 'が必要' + ending + '。' + TAIL)
    frame = out.source_meaning.personal_evaluations[-1]
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert '選びたい' not in out.artifact.piece_text
    assert out.artifact.piece_text.count('必要') == 1
    check_bindings(out, text, heads, target)


@pytest.mark.parametrize('scope', ('日程が合うなら、', '日程が合うけれど、', '以前は、'))
@pytest.mark.parametrize('operator', ('より', 'と'))
def test_explicit_scope_contains_the_entire_pair_not_one_operand(scope, operator):
    heads = ('時間', 'こと')
    target = argument(heads, operator)
    text = intro() + scope + '私にとって' + target + 'が必要ではなかったかもしれない。' + TAIL
    out = generated(text)
    assert scope + '私にとって' in out.artifact.piece_text
    assert target + 'が必要ではなかったかもしれない。' + TAIL in out.artifact.piece_text
    check_bindings(out, text, heads, target)


@pytest.mark.parametrize('gap', ('、', '，', ',', '、  ', ',\t', '、\u3000'))
def test_original_order_delimiters_and_utf8_ranges_survive(gap):
    heads = ('もの', '時間')
    target = argument(heads, 'と', gap)
    text = ' \t' + intro(heads) + '\r\n\u3000私は' + target + 'が苦手でした。 ' + TAIL
    out = generated(text)
    assert '私は、' + target + 'が苦手でした。' in out.artifact.piece_text
    check_bindings(out, text, heads, target)


def test_operand_order_does_not_reorder_or_merge_distinct_antecedents():
    text = intro() + '私はそのことより、この時間が好きかもしれません。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text.endswith('私は、そのことより、この時間が好きかもしれません。' + TAIL)
    assert [ref.antecedent_node_id for ref in out.source_meaning.nominal_references] == ['piece:s2', 'piece:s1']


def test_a_pair_does_not_become_a_new_antecedent_for_later_mentions():
    text = intro() + '私にとってその時間と、このことが必要です。私はその時間が好きです。' + TAIL
    out = generated(text)
    refs = out.source_meaning.nominal_references
    assert [ref.antecedent_node_id for ref in refs] == ['piece:s1', 'piece:s2', 'piece:s1']
    assert out.artifact.piece_text.endswith('私にとって、その時間と、このことが必要です。私は、その時間が好きです。' + TAIL)


def test_both_antecedents_are_publicized_without_replacing_the_joint_target():
    text = ('僕にとって友人の森さんと落ち着いて話す時間が大切です。'
            '僕にとって先輩の原さんへ手紙を書くことが必要です。'
            '僕はその時間と、このことが好きかもしれません。まだ、始める日は決めていません。')
    out = generated(text)
    assert out.artifact.piece_text == ('僕にとって、友人と落ち着いて話す時間が大切です。'
        '僕にとって、先輩へ手紙を書くことが必要です。'
        '僕は、その時間と、このことが好きかもしれません。まだ、始める日は決めていません。')
    assert all(name not in out.artifact.piece_text for name in ('森さん', '原さん'))
    assert len(out.source_meaning.nominal_references) == 2


@pytest.mark.parametrize('text', (
    intro(('時間',)) + '私はその時間より、このことが好きです。' + TAIL,
    '私はその時間と、このことが好きです。' + intro(),
    intro() + '私にとって庭で花を眺める時間が大切です。私はその時間と、このことが好きです。',
    intro() + '友人は散歩する時間を取った。私はその時間より、このことが好きです。',
    intro() + '私はその時間と、この時間が好きです。' + TAIL,
    intro() + '私はその時間より、この時間が好きです。' + TAIL,
    intro() + '私はその時間とこのことが好きです。' + TAIL,
    intro() + '私はその時間よりも、このことが好きです。' + TAIL,
    intro() + '私はその時間と、このことと、そのものが好きです。',
    intro() + '私はその時間より、このことより、そのものが好きです。',
    intro() + '私はその時間と、このことより、そのものが好きです。',
    intro() + '私はその時間ではなく、このことが好きです。' + TAIL,
    intro() + '私はその時間帯と、このことが好きです。' + TAIL,
    intro() + '私はその時間を確保することと、このことが好きです。',
))
def test_unbound_ambiguous_same_head_or_nested_pairs_remain_unavailable(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None and out.reason_codes
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('change', ('scalar', 'utf8', 'antecedent', 'edge', 'evaluation'))
def test_both_reference_bindings_are_rederived_before_realization(change):
    text = intro() + '私はその時間と、このことが好きです。' + TAIL
    out = generated(text)
    meaning = out.source_meaning
    first, second = meaning.nominal_references
    if change == 'scalar':
        a, b = second.reference_scalar_span
        meaning = replace(meaning, nominal_references=(first, replace(second, reference_scalar_span=(a-1, b))))
    elif change == 'utf8':
        a, b = second.reference_utf8_span
        meaning = replace(meaning, nominal_references=(first, replace(second, reference_utf8_span=(a+1, b))))
    elif change == 'antecedent':
        meaning = replace(meaning, nominal_references=(first, replace(second, antecedent_node_id='piece:s1')))
    elif change == 'edge':
        edges = tuple(e for e in meaning.graph.edges if e.edge_id != 'piece:reference2')
        meaning = replace(meaning, graph=replace(meaning.graph, edges=edges))
    else:
        frames = meaning.personal_evaluations
        meaning = replace(meaning, personal_evaluations=frames[:-1] + (replace(frames[-1], polarity='NEGATIVE'),))
    with pytest.raises(ValueError):
        compile_piece_artifact_plan(meaning)
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('operator', ('より', 'と'))
def test_same_canonical_body_reaches_both_existing_measured_layouts(ratio, operator):
    class Metrics:
        profile_id = 'synthetic-paired-reference-not-native'
        def graphemes(self, text):
            return list(text)
        def measure(self, text, size):
            advance = len(text) * size
            return TextMeasurement(advance, 0, -.8 * size, advance, .2 * size)
    text = intro() + '私は' + argument(('時間', 'こと'), operator) + 'が好きかもしれません。' + TAIL
    out = generated(text)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    before = deepcopy((candidate, recipe))
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert layout['layout_state'] == 'fit'
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert layout['native_device_verified'] is False
    rejected = run(text, requested_format='declaration')
    assert rejected.status == EngineStatus.UNAVAILABLE and rejected.artifact is None
