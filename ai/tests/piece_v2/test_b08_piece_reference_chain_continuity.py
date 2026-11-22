"""Bounded same-referent chains on the existing disabled Piece author.

Synthetic inputs only. A validated reference is not enough by itself: each
adjacent link must have already retained the same explicit author and target.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TARGET = '湖畔で木々の葉音を静かに聞く時間'
TAIL = 'まだ、毎週通えるとは限らない。'
SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
PREDICATES = ('好きです', '苦手だった', '好きではない',
              '苦手じゃなかった', '好きかもしれない',
              '好きではなかったかもしれない')


def outcome(text, *, tier='free', requested=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-reference-chain', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-reference-chain', source, source.owner_id,
        source.saved_input_id, source.source_version, tier, requested))
    return source, out


def assert_body(text, expected):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode()
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for group in plan.block_node_ids for n in group) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode()[evidence.utf8_start:evidence.utf8_end] == node.value.encode()
    snapshot = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == snapshot
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                       candidate['piece_text_hash']) == expected
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    return out


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('predicate', PREDICATES)
def test_chain_uses_source_bound_target_not_surface_pronoun_equality(speaker, predicate):
    text = (f'{speaker}にとって{TARGET}が大切。{speaker}はその時間が好き。'
            f'{speaker}はこの時間が{predicate}。{TAIL}')
    expected = f'{speaker}にとって、{TARGET}が大切。その時間が好き。この時間が{predicate}。{TAIL}'
    out = assert_body(text, expected)
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert refs[0].antecedent_node_id == refs[1].antecedent_node_id == 'piece:s1'
    assert refs[0].antecedent_scalar_span == refs[1].antecedent_scalar_span
    assert refs[0].antecedent_utf8_span == refs[1].antecedent_utf8_span
    assert refs[0].reference_scalar_span != refs[1].reference_scalar_span


@pytest.mark.parametrize('target,head', (
    (TARGET, '時間'), ('🌱を窓辺で眺めること', 'こと'), ('自分で選んだもの', 'もの')))
@pytest.mark.parametrize('count', (3, 4, 5))
def test_every_adjacent_link_preserves_all_propositions_and_reservation(target, head, count):
    clauses = [f'その{head}が好き。', f'この{head}が苦手ではない。',
               f'その{head}が好きだった。', f'この{head}が好きかもしれない。'][:count-1]
    assert_body('僕にとって' + target + 'が大切。' + ''.join('僕は' + c for c in clauses) + TAIL,
                '僕にとって、' + target + 'が大切。' + ''.join(clauses) + TAIL)


@pytest.mark.parametrize('opening,canonical', (
    (f'僕が大切にしたいのは、{TARGET}です。', f'僕は、{TARGET}を大切にしたい。'),
    (f'僕は{TARGET}が苦手だった。', f'僕は、{TARGET}が苦手だった。'),
    ('僕にとって友人の青木さんの同僚の木村さんと落ち着いて話す時間が大切。',
     '僕にとって、友人の同僚と落ち着いて話す時間が大切。'),
))
def test_existing_established_viewpoint_and_public_role_stay(opening, canonical):
    assert_body(opening + f'僕はその時間が好き。僕はこの時間が苦手ではない。{TAIL}',
                canonical + f'その時間が好き。この時間が苦手ではない。{TAIL}')


@pytest.mark.parametrize('gap', ('\n', '\r\n', '\n\n'))
@pytest.mark.parametrize('boundary', (1, 2))
def test_line_break_stops_chain_and_does_not_reestablish_by_nearness(gap, boundary):
    first = f'私にとって{TARGET}が大切。'
    second = '私はその時間が好き。'
    third = '私はこの時間が苦手ではない。'
    text = first + (gap if boundary == 1 else '') + second + (gap if boundary == 2 else '') + third + TAIL
    expected = (f'私にとって、{TARGET}が大切。' +
                ('私は、その時間が好き。' if boundary == 1 else 'その時間が好き。') +
                '私は、この時間が苦手ではない。' + TAIL)
    assert_body(text, expected)


@pytest.mark.parametrize('middle,canonical', (
    ('僕はその時間が好き。', '僕は、その時間が好き。'),
    ('私にとってその時間が必要。', '私にとって、その時間が必要。'),
    ('私が好きなのはその時間です。', '私は、その時間が好きです。'),
    ('予定が空くなら、私はその時間が好き。', '予定が空くなら、私は、その時間が好き。'),
    ('私はその時間より、庭で花を眺めることが好き。', '私は、その時間より、庭で花を眺めることが好き。'),
    ('昨日は雨が降った。', '昨日は雨が降った。'),
))
def test_noncontinuing_middle_cannot_license_later_topic_deletion(middle, canonical):
    assert_body(f'私にとって{TARGET}が大切。' + middle + f'私はこの時間が苦手ではない。{TAIL}',
                f'私にとって、{TARGET}が大切。' + canonical + f'私は、この時間が苦手ではない。{TAIL}')


@pytest.mark.parametrize('last,canonical', (
    ('僕はこの時間が苦手ではない。', '僕は、この時間が苦手ではない。'),
    ('私にとってこの時間が必要。', '私にとって、この時間が必要。'),
    ('私が好きなのはこの時間です。', '私は、この時間が好きです。'),
    ('予定が空くなら、私はこの時間が好き。', '予定が空くなら、私は、この時間が好き。'),
    ('私はこの時間より、庭で花を眺める時間が好き。', '私は、この時間より、庭で花を眺める時間が好き。'),
))
def test_new_author_viewpoint_focus_scope_and_comparison_stay(last, canonical):
    assert_body(f'私にとって{TARGET}が大切。私はその時間が好き。' + last + TAIL,
                f'私にとって、{TARGET}が大切。その時間が好き。' + canonical + TAIL)


def test_unmodelled_intervening_mention_remains_unavailable():
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。自由な時間もある。私はこの時間が好き。{TAIL}')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


def test_shortest_chain_does_not_lose_old_omission_or_exceed_minimum():
    assert_body('私はものが好き。私はそのものが好き。私はこのものが苦手。',
                '私は、ものが好き。そのものが好き。このものが苦手。')


@pytest.mark.parametrize('damage', ('root_node', 'root_scalar', 'root_utf8', 'mention', 'duty'))
def test_validators_still_reject_tampered_chain_authority(damage):
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。私はこの時間が苦手ではない。{TAIL}')
    meaning, plan = out.source_meaning, out.artifact_plan
    refs = list(meaning.nominal_references)
    if damage == 'duty':
        plan = replace(plan, duties=plan.duties[:-1])
    else:
        changes = {
            'root_node': {'antecedent_node_id': 'piece:s2'},
            'root_scalar': {'antecedent_scalar_span': refs[0].reference_scalar_span},
            'root_utf8': {'antecedent_utf8_span': refs[0].reference_utf8_span},
            'mention': {'reference_scalar_span': refs[0].reference_scalar_span},
        }
        refs[1] = replace(refs[1], **changes[damage])
        meaning = replace(meaning, nominal_references=tuple(refs))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_complete_chain_body_reaches_b9(ratio):
    class Metrics:
        profile_id = 'synthetic-reference-chain-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。私はこの時間が苦手ではない。{TAIL}')
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(candidate['content_payload']['body_blocks']))] == candidate['content_payload']['body_blocks']
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['clipped'] and not layout['native_device_verified']


@pytest.mark.parametrize('extra', ('', '私はこの時間が苦手ではない。'))
def test_identical_sentence_is_not_created_and_declined_link_breaks_chain(extra):
    assert_body(f'私にとって{TARGET}が大切。私はその時間が好き。私はその時間が好き。' + extra + TAIL,
                f'私にとって、{TARGET}が大切。その時間が好き。私は、その時間が好き。' +
                ('私は、この時間が苦手ではない。' if extra else '') + TAIL)


def test_new_speaker_cannot_restart_chain_against_another_authors_root():
    assert_body(f'私にとって{TARGET}が大切。僕はその時間が好き。僕はこの時間が苦手ではない。{TAIL}',
                f'私にとって、{TARGET}が大切。僕は、その時間が好き。僕は、この時間が苦手ではない。{TAIL}')
