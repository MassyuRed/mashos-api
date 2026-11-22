"""Source-bound degree qualifiers on existing disabled Piece evaluations.

Synthetic inputs only. The whole written predicate remains one original
argument. No adverb is assigned an inferred numerical strength or stripped
from negation, time, modality, explicit scope or a publicized relationship.
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

TARGET = '棚で古い写真を見返す時間'
TAIL = 'まだ、毎晩続けられるとは限らない。'
QUALIFIERS = ('とても', 'かなり', '少し', 'あまり')
BASES = ('大切', '大事', '重要', '必要', '好き', '苦手')
SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-degree', '1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-degree', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, result


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
    for frame in meaning.personal_evaluations:
        for (a, b), (c, d) in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert text[a:b].encode() == text.encode()[c:d]
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                      candidate['piece_text_hash']) == expected
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


def clause(speaker, predicate, *, order='finite', kind='preference', target=TARGET):
    if order == 'focus':
        construction = 'が' if kind == 'preference' else 'にとって'
        return speaker + construction + predicate + 'のは' + target + 'です。'
    construction = 'は' if kind == 'preference' else 'にとって'
    return speaker + construction + target + 'が' + predicate + '。'


@pytest.mark.parametrize('qualifier', QUALIFIERS)
@pytest.mark.parametrize('base', BASES)
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_complete_qualified_predicate_is_source_bound_in_both_word_orders(qualifier, base, order):
    kind = 'preference' if base in ('好き', '苦手') else 'value'
    predicate = qualifier + base + ('な' if order == 'focus' else 'です')
    text = clause('私', predicate, order=order, kind=kind) + TAIL
    viewpoint = '私は、' if kind == 'preference' else '私にとって、'
    out = assert_body(text, viewpoint + TARGET + 'が' + qualifier + base + 'です。' + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert text[slice(*frame.scalar_parts[1])] == predicate
    assert frame.kind == ('PERSONAL_PREFERENCE' if kind == 'preference' else 'PERSONAL_VALUE')
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (
        'AFFIRMATIVE', 'NONPAST', 'ASSERTED')


STATES = (
    ('少し苦手だった', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('あまり好きではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('あまり好きじゃなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('かなり好きかもしれない', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('とても好きだったかもしれない', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('あまり好きではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('少し苦手とは限らない', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('あまり好きではないとは限らない', 'NEGATIVE', 'NONPAST', 'NON_UNIVERSAL'),
)


@pytest.mark.parametrize('predicate,polarity,time,commitment', STATES)
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_qualifier_does_not_reset_negation_time_or_modal_commitment(predicate, polarity, time, commitment, order):
    text = clause('僕', predicate, order=order) + TAIL
    out = assert_body(text, '僕は、' + TARGET + 'が' + predicate + '。' + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert text[slice(*frame.scalar_parts[1])] == predicate
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_source_author_and_non_bmp_target_are_kept(speaker, order):
    target = '🌱を紙に描いて残すこと'
    predicate = '少し苦手な' if order == 'focus' else '少し苦手です'
    assert_body(clause(speaker, predicate, order=order, target=target) + TAIL,
                speaker + 'は、' + target + 'が少し苦手です。' + TAIL)


@pytest.mark.parametrize('premise,relation', (
    ('静かな場所なので', 'SOURCE_EXPLICIT_REASON'),
    ('予定が空くなら', 'SOURCE_EXPLICIT_CONDITION'),
    ('毎晩は難しいけれど', 'SOURCE_EXPLICIT_CONCESSION'),
))
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_written_scope_stays_before_the_whole_qualified_evaluation(premise, relation, order):
    text = premise + '、' + clause('僕', '少し苦手だった', order=order) + TAIL
    out = assert_body(text, premise + '、僕は、' + TARGET + 'が少し苦手だった。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == relation
    assert text[slice(*scope.scope_scalar_span)] == premise
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('qualifier', QUALIFIERS)
def test_reference_keeps_its_own_degree_and_negation_not_its_antecedents(qualifier):
    text = ('私にとって' + TARGET + 'がとても大切です。'
            '私はその時間が' + qualifier + '好きではなかったかもしれない。' + TAIL)
    expected = ('私にとって、' + TARGET + 'がとても大切です。その時間が'
                + qualifier + '好きではなかったかもしれない。' + TAIL)
    out = assert_body(text, expected)
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == 'piece:s1' and ref.reference_node_id == 'piece:s2'
    assert text[slice(*ref.antecedent_scalar_span)] == TARGET
    assert text[slice(*ref.reference_scalar_span)] == 'その時間'
    frame = out.source_meaning.personal_evaluations[1]
    assert text[slice(*frame.scalar_parts[1])] == qualifier + '好きではなかったかもしれない'


@pytest.mark.parametrize('target', ('少し前に集めたもの', 'とても静かな場所で過ごす時間', TARGET))
def test_modifier_inside_the_target_is_not_extracted_as_predicate_degree(target):
    text = '私は' + target + 'が好きです。' + TAIL
    out = assert_body(text, '私は、' + target + 'が好きです。' + TAIL)
    frame, = out.source_meaning.personal_evaluations
    assert text[slice(*frame.scalar_parts[1])] == '好きです'
    assert text[slice(*frame.scalar_parts[2])] == target


@pytest.mark.parametrize('text', (
    '私は' + TARGET + 'がたぶん好きです。',
    '私は' + TARGET + 'がいつも好きです。',
    '私は' + TARGET + 'がとても少し好きです。',
    '私は' + TARGET + 'がほんの少し苦手です。',
    '少し私は' + TARGET + 'が好きです。',
    TARGET + 'がとても好きです。',
    '彼は' + TARGET + 'がとても好きです。',
    '私は' + TARGET + 'がとても大切です。',
    '私がとても好きなのは友人です。',
    '私はその時間がとても好きです。',
    '私は' + TARGET + 'が少し苦手だと聞いた。',
    '私は「とても好き」と言われた。',
))
def test_unmodelled_scope_authorship_reference_or_report_is_not_admitted(text):
    _, out = outcome(text + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('damage', ('scalar_cut', 'utf8_cut', 'both_cuts', 'polarity', 'time', 'commitment'))
def test_qualifier_cannot_be_removed_from_metadata_or_its_predicate_reinterpreted(damage):
    text = '僕は' + TARGET + 'があまり好きではなかったかもしれない。' + TAIL
    out = assert_body(text, '僕は、' + TARGET + 'があまり好きではなかったかもしれない。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    frame, = meaning.personal_evaluations
    scalar, utf8 = list(frame.scalar_parts), list(frame.utf8_parts)
    if damage in ('scalar_cut', 'both_cuts'):
        scalar[1] = scalar[1][0] + len('あまり'), scalar[1][1]
    if damage in ('utf8_cut', 'both_cuts'):
        utf8[1] = utf8[1][0] + len('あまり'.encode()), utf8[1][1]
    changes = {'scalar_parts': tuple(scalar), 'utf8_parts': tuple(utf8)}
    changes.update({'polarity': {'polarity': 'AFFIRMATIVE'},
                    'time': {'temporal_scope': 'NONPAST'},
                    'commitment': {'commitment': 'ASSERTED'}}.get(damage, {}))
    tampered = replace(meaning, personal_evaluations=(replace(frame, **changes),))
    with pytest.raises(ValueError):
        realize_piece_artifact(tampered, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('qualifier', QUALIFIERS)
def test_complete_qualified_body_and_hash_reach_unchanged_b9(ratio, qualifier):
    class Metrics:
        profile_id = 'synthetic-degree-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)
    text = '僕は' + TARGET + 'が' + qualifier + '好きです。' + TAIL
    out = assert_body(text, '僕は、' + TARGET + 'が' + qualifier + '好きです。' + TAIL)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(candidate['content_payload']['body_blocks']))] == candidate['content_payload']['body_blocks']
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['clipped'] and not layout['native_device_verified']
