"""Explicit two-reference operators do not require an editorial comma."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import itertools

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

OBJECTS = {
    '時間': '庭で静かに鳥の声を聞く時間',
    'こと': '自分の考えをノートに書くこと',
    'もの': '長く手元で使ってきたもの',
}
TAIL = 'まだ、毎日続けるかは決めていません。'


def introduction(heads=('時間', 'こと'), speaker='僕'):
    return ''.join(speaker + 'にとって' + OBJECTS[h] + 'が大切です。' for h in heads)


def run(text, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-no-comma-pair', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-no-comma-pair', source, source.owner_id,
        source.saved_input_id, source.source_version, tier=tier,
        requested_format=requested_format))
    return source, out


def generated(text, tier='free'):
    source, out = run(text, tier)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    candidate = out.artifact.as_candidate()
    assert generate_piece_candidate(source, authenticated_owner_id=source.owner_id, tier=tier) == candidate
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert out.automatic_progression is False
    assert candidate['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert out.source_meaning.envelope.raw_utf8 == text.encode()
    return out


def check_pair(out, text, heads, target):
    meaning, plan = out.source_meaning, out.artifact_plan
    refs = meaning.nominal_references
    assert len(refs) == 2
    for index, (ref, head) in enumerate(zip(refs, heads, strict=True)):
        assert ref.antecedent_node_id == 'piece:s' + str(index + 1)
        assert ref.reference_node_id == 'piece:s3'
        assert text[slice(*ref.antecedent_scalar_span)] == OBJECTS[head]
        assert text.encode()[slice(*ref.antecedent_utf8_span)].decode() == OBJECTS[head]
        mention = ('その' if index == 0 else 'この') + head
        assert text[slice(*ref.reference_scalar_span)] == mention
        assert text.encode()[slice(*ref.reference_utf8_span)].decode() == mention
    frame = meaning.personal_evaluations[-1]
    assert len(meaning.personal_evaluations) == 3
    assert text[slice(*frame.scalar_parts[2])] == target
    assert text.encode()[slice(*frame.utf8_parts[2])].decode() == target
    edges = [e for e in meaning.graph.edges if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']
    assert [e.target_node_id for e in edges] == ['piece:s1', 'piece:s2']
    assert [e.evidence_ids for e in edges] == [('piece:e1', 'piece:e3'), ('piece:e2', 'piece:e3')]
    assert plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3', 'piece:s4'),)
    assert target in out.artifact.piece_text
    assert out.artifact.piece_text.endswith(TAIL)
    saved = deepcopy((asdict(meaning), asdict(plan)))
    assert realize_piece_artifact(meaning, plan, tier='free', requested_format=None) == out.artifact
    assert (asdict(meaning), asdict(plan)) == saved


@pytest.mark.parametrize('heads', tuple(itertools.permutations(OBJECTS, 2)))
@pytest.mark.parametrize('operator', ('と', 'より'))
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_written_operator_binds_two_whole_operands_without_a_comma(heads, operator, order):
    target = 'その' + heads[0] + operator + 'この' + heads[1]
    last = ('僕は' + target + 'が好きです。' if order == 'finite'
            else '僕が好きなのは、' + target + 'です。')
    text = introduction(heads) + last + TAIL
    out = generated(text)
    check_pair(out, text, heads, target)
    prefix = ''.join('僕にとって、' + OBJECTS[h] + 'が大切です。' for h in heads)
    expected = prefix + ('' if order == 'finite' else '僕は、') + target + 'が好きです。' + TAIL
    assert out.artifact.piece_text == expected


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_existing_author_continuity_and_explicit_value_viewpoints_are_preserved(speaker):
    target = 'その時間とこのこと'
    text = (speaker + 'にとって' + OBJECTS['時間'] + 'が大切です。'
            + speaker + 'が大切にしたいのは、' + OBJECTS['こと'] + 'です。'
            + speaker + 'は' + target + 'が好きかもしれません。' + TAIL)
    out = generated(text)
    assert out.artifact.piece_text == (speaker + 'にとって、' + OBJECTS['時間'] + 'が大切です。'
            + OBJECTS['こと'] + 'を大切にしたい。' + target + 'が好きかもしれません。' + TAIL)
    assert len(out.source_meaning.nominal_references) == 2


@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('operator', ('と', 'より'))
def test_horizontal_gap_is_preserved_not_inserted_or_normalized(gap, operator):
    target = 'そのもの' + operator + gap + 'この時間'
    text = ' \t' + introduction(('もの', '時間')) + '\r\n\u3000僕は' + target + 'が好きです。' + TAIL
    out = generated(text)
    check_pair(out, text, ('もの', '時間'), target)
    assert '僕は、' + target + 'が好きです。' in out.artifact.piece_text  # Keep the newline barrier.


@pytest.mark.parametrize('ending,polarity,time,commitment', (
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('かもしれません', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('とは限りません', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
))
@pytest.mark.parametrize('operator', ('と', 'より'))
def test_evaluation_scope_still_covers_the_complete_pair(ending, polarity, time, commitment, operator):
    target = 'その時間' + operator + 'このこと'
    text = introduction() + '僕にとって' + target + 'が必要' + ending + '。' + TAIL
    out = generated(text)
    check_pair(out, text, ('時間', 'こと'), target)
    frame = out.source_meaning.personal_evaluations[-1]
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert out.artifact.piece_text.endswith('僕にとって、' + target + 'が必要' + ending + '。' + TAIL)
    assert '選びたい' not in out.artifact.piece_text


@pytest.mark.parametrize('scope', ('以前は、', '今も、', '日程が合うなら、', '日程が合うけれど、'))
def test_time_and_condition_are_not_absorbed_into_one_operand(scope):
    target = 'その時間よりこのこと'
    text = introduction() + scope + '僕にとって' + target + 'が必要ではなかったかもしれない。' + TAIL
    out = generated(text)
    check_pair(out, text, ('時間', 'こと'), target)
    assert scope + '僕にとって' in out.artifact.piece_text
    assert target + 'が必要ではなかったかもしれない。' + TAIL in out.artifact.piece_text
    assert len(out.source_meaning.expression_scopes) == 1


def test_source_bound_names_keep_both_roles_in_the_existing_writer():
    text = ('僕にとって友人の東さんと落ち着いて話す時間が大切です。'
            '僕が大切にしたいのは、先輩の南さんへ手紙を書くことです。'
            '僕はその時間とこのことが好きかもしれません。まだ、始める日は決めていません。')
    out = generated(text)
    assert out.artifact.piece_text == ('僕にとって、友人と落ち着いて話す時間が大切です。'
            '先輩へ手紙を書くことを大切にしたい。その時間とこのことが好きかもしれません。'
            'まだ、始める日は決めていません。')
    assert len(out.source_meaning.role_bindings) == 2
    assert len(out.source_meaning.nominal_references) == 2
    assert all(name not in out.artifact.piece_text for name in ('東さん', '南さん'))


@pytest.mark.parametrize('target', (
    'その時間このこと', 'その時間、このこと', 'その時間とこの時間',
    'その時間よりこの時間', 'その時間よりもこのこと', 'その時間とてもこのこと',
    'その時間とこのこととそのもの', 'その時間よりこのことよりそのもの',
    'その時間とこのことより、そのもの', 'その時間帯とこのこと',
    'その時間を確保することとこのこと', 'その時間ではなくこのこと',
    'その時間と\nこのこと', 'その時間と\rこのこと',
    'その時間と、このこととそのもの',
))
def test_missing_operators_same_heads_and_nested_operands_do_not_gain_authority(target):
    _, out = run(introduction() + '僕は' + target + 'が好きです。' + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('prefix', (
    introduction(('時間',)),
    '',
    introduction() + '僕にとって駅で待つ時間が大切です。',
    introduction() + '友人は散歩する時間を取った。',
))
def test_a_written_pair_cannot_certify_missing_or_ambiguous_antecedents(prefix):
    _, out = run(prefix + '僕はその時間とこのことが好きです。' + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('target', ('その時間より朝に手紙を書くこと', '朝に手紙を書くことよりこの時間'))
def test_new_compact_grammar_does_not_expand_single_reference_comparisons(target):
    _, out = run(introduction(('時間',)) + '僕は' + target + 'が好きです。' + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('change', ('scalar', 'utf8', 'antecedent', 'edge', 'evaluation'))
def test_existing_source_validators_rederive_both_operand_bindings(change):
    text = introduction() + '僕はその時間とこのことが好きです。' + TAIL
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
        meaning = replace(meaning, graph=replace(meaning.graph, edges=meaning.graph.edges[:-1]))
    else:
        frames = meaning.personal_evaluations
        meaning = replace(meaning, personal_evaluations=frames[:-1] + (replace(frames[-1], polarity='NEGATIVE'),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_existing_layout_consumes_the_canonical_body_without_record_effects(tier, ratio):
    text = introduction() + '僕はその時間とこのことが好きかもしれません。' + TAIL
    out = generated(text, tier)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    class Metrics:
        profile_id = 'synthetic-no-comma-pair-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, size):
            a = len(text) * size
            return TextMeasurement(a, 0, -.8 * size, a, .2 * size)
    frozen = deepcopy((candidate, recipe))
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == frozen
    assert layout['layout_state'] == 'fit'
    assert not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(candidate['content_payload']['body_blocks']))] == candidate['content_payload']['body_blocks']
    assert run(text, tier='premium', requested_format='declaration')[1].status == EngineStatus.UNAVAILABLE
