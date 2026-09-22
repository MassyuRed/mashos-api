"""Synthetic same-author evaluation continuity on the existing CMEE Piece path.

Only the repeated self-topic of an adjacent, uniquely bound preference may be
omitted. Source meaning, viewpoint, predicates and reservations are retained.
No source admission, activation, authentication or native-export capability.
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

TARGET = '海辺で波の音を静かに聞く時間'
TAIL = 'まだ、毎週通えるとは限らない。'
SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
PREDICATES = ('好き', '苦手', '好きです', '好きだった', '好きではない',
              '苦手じゃなかった', '好きかもしれない', '好きとは限らない',
              '好きではなかったかもしれない')


def outcome(text, *, tier='free', requested=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-evaluation-continuity', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-evaluation-continuity', source, source.owner_id,
        source.saved_input_id, source.source_version, tier, requested))
    return source, out


def assert_body(text, expected):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert compile_piece_artifact_plan(meaning) == plan
    assert [d.node_id for d in plan.duties] == [n.node_id for n in meaning.graph.nodes]
    assert tuple(n for group in plan.block_node_ids for n in group) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                       candidate['piece_text_hash']) == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('predicate', PREDICATES)
def test_viewpoint_stays_and_bound_preference_omits_only_repeated_topic(speaker, predicate):
    text = f'{speaker}にとって{TARGET}が大切。{speaker}はその時間が{predicate}。{TAIL}'
    expected = f'{speaker}にとって、{TARGET}が大切。その時間が{predicate}。{TAIL}'
    out = assert_body(text, expected)
    assert len(out.source_meaning.personal_evaluations) == 2
    assert len(out.source_meaning.nominal_references) == 1


@pytest.mark.parametrize('first', ('苦手だった', '好きではなかった', '好きかもしれない'))
def test_plain_topic_preference_can_establish_the_same_author(first):
    assert_body(f'私は{TARGET}が{first}。私はその時間が好きです。{TAIL}',
                f'私は、{TARGET}が{first}。その時間が好きです。{TAIL}')


@pytest.mark.parametrize('gap', ('', ' ', '\t', '\u3000'))
def test_non_line_whitespace_does_not_break_source_adjacency(gap):
    assert_body(f'僕にとって{TARGET}が大切。{gap}僕はその時間が好き。{TAIL}',
                f'僕にとって、{TARGET}が大切。その時間が好き。{TAIL}')


PRESERVED = (
    ('other_author', f'私にとって{TARGET}が大切。僕はその時間が好き。{TAIL}',
     f'私にとって、{TARGET}が大切。僕は、その時間が好き。{TAIL}'),
    ('next_viewpoint', f'私にとって{TARGET}が大切。私にとってその時間が必要。{TAIL}',
     f'私にとって、{TARGET}が大切。私にとって、その時間が必要。{TAIL}'),
    ('next_focus', f'私にとって{TARGET}が大切。私が好きなのはその時間です。{TAIL}',
     f'私にとって、{TARGET}が大切。私は、その時間が好きです。{TAIL}'),
    ('comparison', f'私にとって{TARGET}が大切。私はその時間より、森で風の音を聞く時間が好き。{TAIL}',
     f'私にとって、{TARGET}が大切。私は、その時間より、森で風の音を聞く時間が好き。{TAIL}'),
    ('unlinked_object', f'私にとって{TARGET}が大切。私は森で風の音を聞く時間が好き。{TAIL}',
     f'私にとって、{TARGET}が大切。私は、森で風の音を聞く時間が好き。{TAIL}'),
    ('intervening_context', f'私にとって{TARGET}が大切。昨日は雨が降った。私はその時間が好き。{TAIL}',
     f'私にとって、{TARGET}が大切。昨日は雨が降った。私は、その時間が好き。{TAIL}'),
    ('prior_condition', f'予定が空くなら、私にとって{TARGET}が大切。私はその時間が好き。{TAIL}',
     f'予定が空くなら、私にとって、{TARGET}が大切。私は、その時間が好き。{TAIL}'),
    ('next_condition', f'私にとって{TARGET}が大切。予定が空くなら、私はその時間が好き。{TAIL}',
     f'私にとって、{TARGET}が大切。予定が空くなら、私は、その時間が好き。{TAIL}'),
    ('prior_other_subject', f'私にとって友人が戻ってくる時間が大切。私はその時間が好き。{TAIL}',
     f'私にとって、友人が戻ってくる時間が大切。私は、その時間が好き。{TAIL}'),
    ('prior_contrast', f'私にとって夜は静かに過ごす時間が大切。私はその時間が好き。{TAIL}',
     f'私にとって、夜は静かに過ごす時間が大切。私は、その時間が好き。{TAIL}'),
    ('reference_chain_not_directly_adjacent', f'私にとって{TARGET}が大切。私はその時間が好き。私はその時間が苦手ではない。{TAIL}',
     f'私にとって、{TARGET}が大切。その時間が好き。私は、その時間が苦手ではない。{TAIL}'),
)


@pytest.mark.parametrize('case,text,expected', PRESERVED, ids=[r[0] for r in PRESERVED])
def test_other_authors_scopes_comparisons_and_viewpoints_are_not_elided(case, text, expected):
    assert_body(text, expected)


@pytest.mark.parametrize('gap', ('\n', '\r\n', '\n\n'))
def test_written_line_boundary_keeps_topic(gap):
    assert_body(f'私にとって{TARGET}が大切。{gap}私はその時間が好き。{TAIL}',
                f'私にとって、{TARGET}が大切。私は、その時間が好き。{TAIL}')


@pytest.mark.parametrize('tier,requested', (('free', None), ('plus', None),
                                           ('premium', None), ('premium', 'short_essay')))
def test_tiers_share_the_same_complete_body(tier, requested):
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。{TAIL}',
                     tier=tier, requested=requested)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == f'私にとって、{TARGET}が大切。その時間が好き。{TAIL}'


@pytest.mark.parametrize('tier,requested', (('free', 'short_essay'), ('plus', 'short_essay'),
                                           ('premium', 'quote'), ('premium', 'declaration')))
def test_optional_edit_cannot_grant_a_format(tier, requested):
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。{TAIL}',
                     tier=tier, requested=requested)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('damage', ('reference', 'speaker', 'predicate', 'scope', 'drop_duty'))
def test_editorial_choice_cannot_license_tampered_meaning_or_plan(damage):
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。{TAIL}')
    meaning, plan = out.source_meaning, out.artifact_plan
    if damage == 'drop_duty':
        plan = replace(plan, duties=plan.duties[:-1])
    elif damage == 'reference':
        ref = replace(meaning.nominal_references[0], antecedent_node_id='piece:foreign')
        meaning = replace(meaning, nominal_references=(ref,))
    elif damage == 'scope':
        meaning = replace(meaning, expression_scopes=(object(),))
    else:
        frame = meaning.personal_evaluations[1]
        parts = list(frame.scalar_parts)
        part = 0 if damage == 'speaker' else 1
        parts[part] = (parts[part][0] + 1, parts[part][1])
        frame = replace(frame, scalar_parts=tuple(parts))
        meaning = replace(meaning, personal_evaluations=(meaning.personal_evaluations[0], frame))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_b9_consumes_exact_edited_canonical_body(ratio):
    class Metrics:
        profile_id = 'synthetic-evaluation-continuity-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            w = len(text) * font_px
            return TextMeasurement(w, 0, -font_px * .8, w, font_px * .2)
    _, out = outcome(f'私にとって{TARGET}が大切。私はその時間が好き。{TAIL}')
    c = out.artifact.as_candidate()
    recipe = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = c['content_payload']['body_blocks']
    assert [''.join(l['text'] for l in layout['lines'] if l['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert layout['piece_text_hash'] == c['piece_text_hash']
    assert not layout['clipped'] and not layout['native_device_verified']
