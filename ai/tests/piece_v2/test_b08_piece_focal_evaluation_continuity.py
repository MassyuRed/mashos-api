"""A focal author can continue into an adjacent, bound preference.

Synthetic only. The edit removes one redundant topic, not a source node,
viewpoint-qualified value, evaluation, relationship, or qualification.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
TARGET = '窓辺で草花を眺めて過ごす時間'
TAIL = 'まだ、毎日予定を空けられるとは限らない。'
ENDINGS = (
    ('です', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('だったかもしれない', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('とは限らない', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('じゃなかったとは限らない', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
)


def focal(speaker='僕', target=TARGET, predicate='大切にしたい'):
    return speaker + 'が' + predicate + 'のは、' + target + 'です。'


def run(text, **kwargs):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-focal-evaluation', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-continuity', source, source.owner_id, source.saved_input_id,
        source.source_version, **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('demonstrative', ('その', 'この'))
@pytest.mark.parametrize('ending,polarity,time,commitment', ENDINGS)
def test_bound_preference_keeps_its_own_state_without_repeating_focal_topic(
        speaker, demonstrative, ending, polarity, time, commitment):
    second = speaker + 'は' + demonstrative + '時間が好き' + ending + '。'
    text = focal(speaker) + second + TAIL
    out = generated(text)
    expected = speaker + 'は、' + TARGET + 'を大切にしたい。' + demonstrative + '時間が好き' + ending + '。' + TAIL
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert tuple(d.operation for d in out.artifact_plan.duties) == (
        'SOURCE_FOCAL_TO_FIRST_PERSON', 'SOURCE_PERSONAL_EVALUATION', 'KEEP_COMPLETE_SOURCE_CONTEXT')
    meaning = out.source_meaning
    assert meaning.envelope.raw_utf8 == text.encode()
    assert meaning.graph.nodes[1].value == second
    frame, = meaning.personal_evaluations
    ref, = meaning.nominal_references
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert text[slice(*frame.scalar_parts[0])] == speaker
    assert ref.reference_scalar_span == frame.scalar_parts[2]
    assert ref.antecedent_node_id == meaning.graph.nodes[0].node_id
    assert text[slice(*ref.antecedent_scalar_span)] == TARGET
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    candidate = out.artifact.as_candidate()
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert candidate['production_enabled'] is False
    assert generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-focal-evaluation', 'v1', text),
        authenticated_owner_id='synthetic-owner') == candidate


@pytest.mark.parametrize('predicate', ('大切にしたい', '大切にしている', '大切にしたくない',
                                     '望んでいる', '望んでいない', '選びたい', '選びたくない'))
def test_focal_predicate_and_its_negation_are_not_inherited_by_preference(predicate):
    text = focal('俺', predicate=predicate) + '俺はその時間が好きではなかったかもしれない。' + TAIL
    expected = '俺は、' + TARGET + 'を' + predicate + '。その時間が好きではなかったかもしれない。' + TAIL
    assert generated(text).artifact.piece_text == expected


@pytest.mark.parametrize('target,head', (
    ('自分の手で小さく試して確かめること', 'こと'),
    ('長く手元で使い続けてきたもの', 'もの'),
    ('友人の林さんの同僚の井上さんと落ち着いて話す時間', '時間'),
))
def test_original_target_and_public_role_chain_survive_topic_omission(target, head):
    text = focal('ぼく', target) + 'ぼくはその' + head + 'が好きです。' + TAIL
    out = generated(text)
    public_target = target.replace('の林さん', '').replace('の井上さん', '')
    assert out.artifact.piece_text == 'ぼくは、' + public_target + 'を大切にしたい。その' + head + 'が好きです。' + TAIL
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target


@pytest.mark.parametrize('gap', ('\n', '\r\n', '\r'))
def test_source_line_break_keeps_explicit_preference_topic(gap):
    text = focal() + gap + '僕はその時間が好きです。' + TAIL
    assert generated(text).artifact.piece_text == '僕は、' + TARGET + 'を大切にしたい。僕は、その時間が好きです。' + TAIL


@pytest.mark.parametrize('first,second', (('私', '僕'), ('僕', '私'), ('わたし', '私'), ('俺', 'おれ')))
def test_different_written_speakers_are_never_merged(first, second):
    text = focal(first) + second + 'はその時間が好きです。' + TAIL
    assert generated(text).artifact.piece_text == first + 'は、' + TARGET + 'を大切にしたい。' + second + 'は、その時間が好きです。' + TAIL


@pytest.mark.parametrize('scope', ('空が明るいなら、', '空が明るいので、', '空が明るいけれど、'))
def test_condition_reason_and_concession_keep_their_own_evaluation_topic(scope):
    text = focal() + scope + '僕はその時間が好きです。' + TAIL
    assert generated(text).artifact.piece_text == '僕は、' + TARGET + 'を大切にしたい。' + scope + '僕は、その時間が好きです。' + TAIL


@pytest.mark.parametrize('middle', ('友人は先に帰った。', '予定を紙に書いておいた。'))
def test_even_noncompeting_intervening_context_does_not_grant_adjacency(middle):
    text = focal() + middle + '僕はその時間が好きです。' + TAIL
    assert generated(text).artifact.piece_text == '僕は、' + TARGET + 'を大切にしたい。' + middle + '僕は、その時間が好きです。' + TAIL


def test_other_subject_inside_focal_target_declines_only_optional_edit():
    target = '母が準備を終えるまで庭を眺める時間'
    text = focal('僕', target) + '僕はその時間が好きです。' + TAIL
    assert generated(text).artifact.piece_text == '僕は、' + target + 'を大切にしたい。僕は、その時間が好きです。' + TAIL


@pytest.mark.parametrize('second,expected', (
    ('僕にとってその時間が必要ではなかったかもしれない。', '僕にとって、その時間が必要ではなかったかもしれない。'),
    ('僕が好きなのは、その時間です。', '僕は、その時間が好きです。'),
    ('僕はその時間は好きです。', '僕はその時間は好きです。'),
    ('僕はその時間が好きだと友人が言った。', '僕はその時間が好きだと友人が言った。'),
))
def test_viewpoint_focus_contrast_and_report_are_not_plain_self_topics(second, expected):
    text = focal() + second + TAIL
    assert generated(text).artifact.piece_text == '僕は、' + TARGET + 'を大切にしたい。' + expected + TAIL


def test_an_explicit_value_viewpoint_does_not_become_a_focal_topic():
    text = '僕にとって' + TARGET + 'が大切です。僕はその時間が好きです。' + TAIL
    assert generated(text).artifact.piece_text == '僕にとって、' + TARGET + 'が大切です。僕は、その時間が好きです。' + TAIL


def test_third_preference_does_not_skip_over_its_direct_predecessor():
    text = focal() + '僕はその時間が好きです。僕はこの時間が苦手でした。' + TAIL
    expected = '僕は、' + TARGET + 'を大切にしたい。その時間が好きです。僕は、この時間が苦手でした。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert len(out.source_meaning.graph.nodes) == 4
    assert len(out.source_meaning.personal_evaluations) == 2


def test_below_minimum_edit_is_declined_without_padding_or_refusal():
    text = 'わたしが選びたいのは、ものだ。わたしはそのものが好きだ。'
    expected = 'わたしは、ものを選びたい。わたしは、そのものが好きだ。'
    shortened = 'わたしは、ものを選びたい。そのものが好きだ。'
    assert len(shortened) < 24 <= len(expected)
    assert generated(text).artifact.piece_text == expected


@pytest.mark.parametrize('mutation', ('speaker', 'reference', 'antecedent', 'target', 'scope', 'duty', 'paragraph'))
def test_omission_cannot_bypass_source_graph_and_plan_validation(mutation):
    out = generated(focal() + '僕はその時間が好きです。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    frame, = meaning.personal_evaluations
    ref, = meaning.nominal_references
    if mutation == 'speaker':
        meaning = replace(meaning, personal_evaluations=(replace(frame, scalar_parts=((0, 1), *frame.scalar_parts[1:])),))
    elif mutation == 'reference':
        meaning = replace(meaning, nominal_references=())
    elif mutation == 'antecedent':
        meaning = replace(meaning, nominal_references=(replace(ref, antecedent_node_id=ref.reference_node_id),))
    elif mutation == 'target':
        meaning = replace(meaning, nominal_references=(replace(ref, reference_scalar_span=(0, 2)),))
    elif mutation == 'scope':
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(meaning.graph.nodes[0], replace(meaning.graph.nodes[1], node_kind='PIECE_SOURCE_CONDITION_SCOPED_EXPRESSION'), *meaning.graph.nodes[2:])))
    elif mutation == 'duty':
        plan = replace(plan, duties=(plan.duties[0], replace(plan.duties[1], operation='KEEP_COMPLETE_SOURCE_CONTEXT'), *plan.duties[2:]))
    else:
        plan = replace(plan, block_node_ids=tuple((n.node_id,) for n in meaning.graph.nodes))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier,fmt', (('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay')))
def test_tiers_share_the_same_grounded_edited_body(tier, fmt):
    text = focal('ぼく') + 'ぼくはその時間が好きです。' + TAIL
    expected = 'ぼくは、' + TARGET + 'を大切にしたい。その時間が好きです。' + TAIL
    assert generated(text, tier=tier, requested_format=fmt).artifact.piece_text == expected


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_existing_layout_receives_exact_canonical_edited_body(ratio):
    class Metrics:
        profile_id = 'synthetic-focal-evaluation-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    candidate = generated(focal() + '僕はその時間が好きです。' + TAIL).artifact.as_candidate()
    validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'], candidate['piece_text_hash'])
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(row['text'] for row in layout['lines']) == candidate['piece_text']
