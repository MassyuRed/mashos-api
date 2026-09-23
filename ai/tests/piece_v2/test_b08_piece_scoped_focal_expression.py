"""Existing focal duties under source-written reason/condition/concession.

Public synthetic fixtures. No runtime activation or universal scope inference.
The original scope, focal author/predicate/object and later reservation remain
one source-ordered reading group, including independently bound references.
"""
from dataclasses import replace
import hashlib

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

TARGET = '机で静かに手帳を開く時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
SCOPES = (
    ('落ち着いて考えられるので', 'ので', 'SOURCE_EXPLICIT_REASON'),
    ('都合が合うなら', 'なら', 'SOURCE_EXPLICIT_CONDITION'),
    ('都合が合うならば', 'ならば', 'SOURCE_EXPLICIT_CONDITION'),
    ('すぐには始められないけれど', 'けれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('すぐには始められないけれども', 'けれども', 'SOURCE_EXPLICIT_CONCESSION'),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'scoped-focal-fixture', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'scoped-focal-fixture', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, out


def generated(text, expected, *, prefix_context=False):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    meaning, plan = out.source_meaning, out.artifact_plan
    raw = text.encode('utf-8')
    assert meaning.envelope.raw_utf8 == raw
    assert compile_piece_artifact_plan(meaning) == plan
    ids = tuple(n.node_id for n in meaning.graph.nodes)
    expected_groups = ((ids[0],), ids[1:]) if prefix_context else (ids,)
    assert plan.block_node_ids == expected_groups
    assert not plan.declaration_eligible
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert raw[ev.utf8_start:ev.utf8_end] == node.value.encode('utf-8')
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('speaker', ('私', 'ぼく', '俺'))
@pytest.mark.parametrize('scope,marker,relation', SCOPES)
def test_written_scope_qualifies_the_complete_focal_expression(speaker, scope, marker, relation):
    focal = speaker + 'が大切にしたいのは、' + TARGET + 'です。'
    out = generated(scope + '、' + focal + TAIL,
                    scope + '、' + speaker + 'は' + TARGET + 'を大切にしたい。' + TAIL)
    assert len(out.source_meaning.expression_scopes) == 1
    bound = out.source_meaning.expression_scopes[0]
    assert (bound.marker, bound.relation) == (marker, relation)
    original = out.source_meaning.envelope.raw_utf8.decode('utf-8')
    assert original[slice(*bound.scope_scalar_span)] == scope
    assert original[slice(*bound.expression_scalar_span)] == focal
    assert out.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'


@pytest.mark.parametrize('predicate', (
    '大切にしたい', '大切にしている', '大切にしたくない',
    '望んでいる', '望んでいない', '選びたい', '選びたくない',
))
@pytest.mark.parametrize('copula', ('です', 'だ'))
def test_existing_predicate_and_negation_are_not_replaced(predicate, copula):
    prefix = '気持ちが整うなら、'
    generated(prefix + 'わたしが' + predicate + 'のは' + TARGET + copula + '。' + TAIL,
              prefix + 'わたしは' + TARGET + 'を' + predicate + '。' + TAIL)


@pytest.mark.parametrize('target,head', (
    (TARGET, '時間'), ('自分の順番で紙を折ること', 'こと'), ('長く使い続けてきたもの', 'もの'),
))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_following_evaluation_binds_the_scoped_object_not_its_condition(target, head, determiner):
    prefix = '都合が合うなら、僕が大切にしたいのは、'
    reference = '僕は' + determiner + head + 'が苦手ではないかもしれません。'
    out = generated(prefix + target + 'です。' + reference + TAIL,
                    '都合が合うなら、僕は' + target + 'を大切にしたい。僕は、'
                    + determiner + head + 'が苦手ではないかもしれません。' + TAIL)
    assert len(out.source_meaning.nominal_references) == 1
    ref = out.source_meaning.nominal_references[0]
    assert ref.antecedent_scalar_span == (len(prefix), len(prefix) + len(target))
    frame = out.source_meaning.personal_evaluations[0]
    assert (frame.polarity, frame.commitment) == ('NEGATIVE', 'POSSIBLE')
    assert ref.reference_scalar_span == frame.scalar_parts[2]
    assert out.artifact.piece_text.startswith('都合が合うなら、僕は')


@pytest.mark.parametrize('comma', ('、', '，', ','))
@pytest.mark.parametrize('gap', (' ', '\t'))
def test_offsets_use_original_unicode_and_sentence_gaps(comma, gap):
    context = '🌱を眺めた。'
    scope = '落ち着いて考えられるので'
    focal = 'おれが選びたいのは、' + TARGET + 'です。'
    text = context + '\r\n\u3000' + scope + comma + gap + focal + '  おれはその時間が好きでした。' + TAIL
    out = generated(text, context + '\n\n' + scope + '、おれは' + TARGET
                    + 'を選びたい。おれは、その時間が好きでした。' + TAIL,
                    prefix_context=True)
    bound = out.source_meaning.expression_scopes[0]
    assert bound.expression_scalar_span[0] == text.index(focal)
    assert bound.scope_scalar_span[0] == text.index(scope)
    assert out.source_meaning.personal_evaluations[0].temporal_scope == 'PAST'


def test_scoped_focal_changes_its_existing_context_duty_without_moving_other_propositions():
    context = '私にとって対話が大切です。'
    source = context + 'すぐには始められないけれど、私が選びたいのは、' + TARGET + 'です。' + TAIL
    out = generated(source, '私にとって、対話が大切です。すぐには始められないけれど、私は'
                    + TARGET + 'を選びたい。' + TAIL)
    assert [d.operation for d in out.artifact_plan.duties] == [
        'SOURCE_PERSONAL_EVALUATION', 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON',
        'KEEP_COMPLETE_SOURCE_CONTEXT']


def test_explicit_role_publicization_happens_after_original_reference_binding():
    target = '同僚の秋山さんと静かに話す時間'
    text = '都合が合うなら、僕が望んでいるのは、' + target + 'です。僕はその時間が好きです。' + TAIL
    out = generated(text, '都合が合うなら、僕は同僚と静かに話す時間を望んでいる。'
                    '僕は、その時間が好きです。' + TAIL)
    ref = out.source_meaning.nominal_references[0]
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert out.source_meaning.role_bindings[0].name == '秋山さん'


def test_a_bound_reference_in_the_premise_and_new_object_keep_separate_roles():
    context = '僕にとって静かに考える時間が必要です。'
    scope = 'その時間が取れるなら'
    target = '自分の考えを手帳に残すこと'
    out = generated(context + scope + '、僕が選びたいのは、' + target + 'です。'
                    '僕はそのことが好きかもしれません。' + TAIL,
                    '僕にとって、静かに考える時間が必要です。' + scope + '、僕は'
                    + target + 'を選びたい。僕は、そのことが好きかもしれません。' + TAIL)
    assert [(r.antecedent_node_id, r.reference_node_id, r.nominal_head)
            for r in out.source_meaning.nominal_references] == [
                ('piece:s1', 'piece:s2', '時間'), ('piece:s2', 'piece:s3', 'こと')]


@pytest.mark.parametrize('text', (
    '今は、私が選びたいのは、' + TARGET + 'です。',
    '都合が合うから、私が選びたいのは、' + TARGET + 'です。',
    '都合が合うなら、先輩が選びたいのは、' + TARGET + 'です。',
    '都合が合うなら、私が選んだのは、' + TARGET + 'です。',
    '都合が合うなら、私が選びたいのは、' + TARGET + 'でした。',
    '都合が合うなら、私が選びたいのは、' + TARGET + 'だと聞いた。',
    '都合が合うなら、私が選びたいのは、彼が望んでいるのは休む時間というものです。',
    '都合が合うなら、私が選びたいのは、それを続けることです。',
    '私は迷っているけれど、私が選びたいのは、' + TARGET + 'です。',
    'その時間が取れるなら、私が選びたいのは、手帳を開くことです。',
    '都合が合うなら、私が選びたいのは、' + TARGET + 'です。'
    '私にとって散歩する時間が必要です。私はその時間が好きです。',
    '都合が合うなら、私が選びたいのは、本を読むことより紙を折ることです。'
    '私はそのことが好きです。',
))
def test_unknown_nested_reported_or_competing_scope_does_not_gain_authority(text):
    assert outcome(text + TAIL)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('scope', 'expression', 'utf8', 'marker', 'relation', 'reference'))
def test_modified_scope_or_reference_cannot_drive_the_writer(mutation):
    text = '都合が合うなら、私が選びたいのは、' + TARGET + 'です。私はその時間が好きです。' + TAIL
    out = generated(text, '都合が合うなら、私は' + TARGET + 'を選びたい。私は、その時間が好きです。' + TAIL)
    meaning = out.source_meaning
    scope = meaning.expression_scopes[0]
    if mutation == 'reference':
        ref = meaning.nominal_references[0]
        meaning = replace(meaning, nominal_references=(replace(
            ref, antecedent_scalar_span=(0, ref.antecedent_scalar_span[1])),))
    else:
        changes = {
            'scope': {'scope_scalar_span': (1, scope.scope_scalar_span[1])},
            'expression': {'expression_scalar_span': (scope.expression_scalar_span[0] + 1,
                                                      scope.expression_scalar_span[1])},
            'utf8': {'expression_utf8_span': scope.expression_scalar_span},
            'marker': {'marker': 'ので'},
            'relation': {'relation': 'SOURCE_EXPLICIT_REASON'},
        }
        meaning = replace(meaning, expression_scopes=(replace(scope, **changes[mutation]),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('requested', ('quote', 'declaration'))
def test_scope_cannot_be_detached_to_offer_a_shorter_format(requested):
    source, out = outcome('都合が合うなら、私が選びたいのは、' + TARGET + 'です。' + TAIL)
    assert out.status == EngineStatus.GENERATED
    with pytest.raises(ValueError):
        generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
                                 tier='premium', requested_format=requested)


class Metrics:
    profile_id = 'scoped-focal-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_the_same_scoped_body_enters_the_existing_measured_image_path(ratio):
    out = generated('都合が合うなら、私が選びたいのは、' + TARGET + 'です。' + TAIL,
                    '都合が合うなら、私は' + TARGET + 'を選びたい。' + TAIL)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    result = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in result['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert result['piece_text_hash'] == candidate['piece_text_hash']
