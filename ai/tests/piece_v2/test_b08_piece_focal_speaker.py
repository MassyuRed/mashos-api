"""The existing focal grammar keeps the written first-person author end to end.

Synthetic tests only. No new predicate, source type, format or public route.
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
# An independent assertion of the existing transitive vocabulary, not an import
# from the implementation that would silently approve future vocabulary growth.
PREDICATES = ('大切にしたい', '大切にしている', '大切にしたくない',
              '望んでいる', '望んでいない', '選びたい', '選びたくない')
TARGET = '自分の手で小さく試して確かめること'
TAIL = 'まだ、始める日は決めていない。'


def run(text, **kwargs):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-focal', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-focal-speaker', source, source.owner_id,
        source.saved_input_id, source.source_version, **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


def focal(speaker='僕', predicate='大切にしたい', target=TARGET):
    return speaker + 'が' + predicate + 'のは、' + target + 'です。'


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('predicate', PREDICATES)
def test_same_focal_operation_retains_each_written_speaker_and_predicate(speaker, predicate):
    text = focal(speaker, predicate) + TAIL
    out = generated(text)
    expected = speaker + 'は、' + TARGET + 'を' + predicate + '。\n\n' + TAIL
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected.split('\n\n')[0], TAIL)
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert tuple(d.operation for d in out.artifact_plan.duties) == (
        'SOURCE_FOCAL_TO_FIRST_PERSON', 'KEEP_COMPLETE_SOURCE_CONTEXT')
    assert not out.artifact_plan.declaration_eligible
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.source_meaning.envelope.raw_utf8 == text.encode()
    assert out.source_meaning.graph.nodes[0].value == focal(speaker, predicate)
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-focal', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert candidate == out.artifact.as_candidate()
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('target,head', (
    ('窓辺で草花を眺めて過ごす時間', '時間'),
    (TARGET, 'こと'),
    ('長く手元で使い続けてきたもの', 'もの'),
))
def test_focal_reference_is_bound_before_its_own_negative_past_evaluation(speaker, target, head):
    text = '  ' + focal(speaker, target=target) + '\r\n' + speaker + 'にとってその' + head + 'が必要ではなかったかもしれない。' + TAIL + '  '
    out = generated(text)
    expected = speaker + 'は、' + target + 'を大切にしたい。' + speaker + 'にとって、その' + head + 'が必要ではなかったかもしれない。' + TAIL
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    meaning = out.source_meaning
    assert meaning.envelope.raw_utf8 == text.encode()
    ref, = meaning.nominal_references
    frame, = meaning.personal_evaluations
    assert ref.antecedent_node_id == meaning.graph.nodes[0].node_id
    assert ref.reference_node_id == frame.node_id
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert ref.reference_scalar_span == frame.scalar_parts[2]
    assert text[slice(*frame.scalar_parts[0])] == speaker
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')
    for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                         (ref.reference_scalar_span, ref.reference_utf8_span),
                         *zip(frame.scalar_parts, frame.utf8_parts)):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('marker', ('なら', 'ならば', 'ので', 'けれど'))
def test_linked_wish_uses_original_focal_speaker_not_a_fixed_pronoun(speaker, marker):
    first = focal(speaker, '望んでいる', '家で静かに過ごす時間')
    scope = 'その時間が取れる' + marker + '、'
    text = first + scope + speaker + 'はゆっくり考えをまとめたい。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == speaker + 'は、家で静かに過ごす時間を望んでいる。' + scope + 'ゆっくり考えをまとめたい。' + TAIL
    bound_scope, = out.source_meaning.expression_scopes
    assert bound_scope.marker == marker
    assert text[slice(*bound_scope.expression_scalar_span)].startswith(speaker + 'は')
    assert out.source_meaning.graph.nodes[1].value == scope + speaker + 'はゆっくり考えをまとめたい。'


@pytest.mark.parametrize('first,second', (('僕', '私'), ('私', '僕'), ('わたし', '私'), ('俺', 'おれ')))
def test_different_written_speakers_are_not_unified_or_elided(first, second):
    text = focal(first, target='家で静かに過ごす時間') + 'その時間が取れるなら、' + second + 'はゆっくり考えをまとめたい。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == first + 'は、家で静かに過ごす時間を大切にしたい。その時間が取れるなら、' + second + 'は、ゆっくり考えをまとめたい。' + TAIL


@pytest.mark.parametrize('middle,scope', (
    ('友人は先に帰った。', 'その時間が取れるなら、'),
    ('', 'その時間に友人が来るなら、'),
    ('', 'その時間も取れるなら、'),
))
def test_intervening_or_competing_subject_does_not_inherit_focal_author(middle, scope):
    text = focal('僕', target='家で静かに過ごす時間') + middle + scope + '僕はゆっくり考えをまとめたい。' + TAIL
    out = generated(text)
    # Initial も belongs to the reference itself and is not a new participant.
    prefix = '' if scope.startswith('その時間も') else '僕は、'
    assert out.artifact.piece_text == '僕は、家で静かに過ごす時間を大切にしたい。' + middle + scope + prefix + 'ゆっくり考えをまとめたい。' + TAIL


def test_names_are_removed_only_after_original_focal_target_and_reference_binding():
    target = '友人の林さんの同僚の井上さんと落ち着いて話す時間'
    text = focal('ぼく', target=target) + 'ぼくはその時間が好きです。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == 'ぼくは、友人の同僚と落ち着いて話す時間を大切にしたい。その時間が好きです。' + TAIL
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert out.source_meaning.envelope.raw_utf8 == text.encode()


@pytest.mark.parametrize('text', (
    '彼が大切にしたいのは、' + TARGET + 'です。',
    '僕たちが大切にしたいのは、' + TARGET + 'です。',
    '大切にしたいのは、' + TARGET + 'です。',
    '僕が大切にしたいのは、' + TARGET + 'でした。',
    '僕が大切にしたいのは、' + TARGET + 'ではない。',
    '僕が大切にしたいのは、' + TARGET + 'かもしれない。',
    '僕が大切にしたいのは、' + TARGET + 'ですと友人が言った。',
    '「僕が大切にしたいのは、' + TARGET + 'です」と言った。',
    '僕が大切にしたいのは、それです。',
    '僕が大切にしたいのは、その時間です。',
    '僕が大切にしたいのは、雨が降るです。',
))
def test_first_person_capture_does_not_admit_unwritten_or_unsupported_meaning(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('mutation', ('source_speaker', 'reference', 'duty', 'blocks', 'intent'))
def test_writer_rechecks_source_and_plan_before_using_focal_speaker(mutation):
    text = focal('僕', target='家で静かに過ごす時間') + '僕はその時間が好きです。' + TAIL
    out = generated(text)
    meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'source_speaker':
        nodes = meaning.graph.nodes
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(replace(nodes[0], value=nodes[0].value.replace('僕が', '私が', 1)), *nodes[1:])))
    elif mutation == 'reference':
        meaning = replace(meaning, nominal_references=())
    elif mutation == 'duty':
        plan = replace(plan, duties=(replace(plan.duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT'), *plan.duties[1:]))
    elif mutation == 'blocks':
        plan = replace(plan, block_node_ids=tuple((n.node_id,) for n in meaning.graph.nodes))
    else:
        plan = replace(plan, intent=replace(plan.intent, authorship='EMLIS_OWNED'))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier,fmt', (('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay')))
def test_tiers_share_the_same_focal_author_body(tier, fmt):
    text = focal('おれ') + TAIL
    assert generated(text, tier=tier, requested_format=fmt).artifact.piece_text == generated(text).artifact.piece_text


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_existing_b9_consumes_every_focal_body_block(ratio):
    class Metrics:
        profile_id = 'synthetic-focal-speaker-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    candidate = generated(focal('わたし') + TAIL).artifact.as_candidate()
    validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'], candidate['piece_text_hash'])
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(line['text'] for line in layout['lines']) == ''.join(candidate['content_payload']['body_blocks'])
