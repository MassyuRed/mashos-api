"""A written focal object can refer back without inheriting a wish or value.

Public synthetic fixtures. The existing resolver, source plan and writer keep
both propositions; a referent is not a new author, fulfilled condition or vow.
"""
from dataclasses import replace
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

TARGETS = (('一人で静かに手帳を開く時間', '時間'),
           ('机で小さな紙を折ること', 'こと'),
           ('長く大切に使い続けてきたもの', 'もの'))
TARGET, HEAD = TARGETS[0]
TAIL = 'まだ、毎朝続けるかは決めていません。'
PREDICATES = ('大切にしたい', '大切にしている', '大切にしたくない',
              '望んでいる', '望んでいない', '選びたい', '選びたくない')
SCOPES = (('落ち着いて考えられるので', 'SOURCE_EXPLICIT_REASON'),
          ('無理なく続けられるなら', 'SOURCE_EXPLICIT_CONDITION'),
          ('無理なく続けられるならば', 'SOURCE_EXPLICIT_CONDITION'),
          ('まだ迷っているけれど', 'SOURCE_EXPLICIT_CONCESSION'),
          ('まだ迷っているけれども', 'SOURCE_EXPLICIT_CONCESSION'))


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'focal-reference', '1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'focal-reference', source, source.owner_id, source.saved_input_id,
        source.source_version))
    return source, result


def generated(text, expected):
    source, result = outcome(text)
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    assert result.artifact.piece_text == expected
    meaning = result.source_meaning
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert result.artifact_plan == compile_piece_artifact_plan(meaning)
    assert not result.artifact_plan.declaration_eligible
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == result.artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not result.automatic_progression and not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return result


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('target,head', TARGETS)
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_focal_object_uses_the_unique_prior_evaluation_argument(speaker, target, head, determiner):
    before = speaker + 'にとって大切なのは、' + target + 'です。'
    focal = speaker + 'が大切にしたいのは、' + determiner + head + 'です。'
    text = before + focal + TAIL
    result = generated(text, speaker + 'にとって、' + target + 'が大切です。'
                       + speaker + 'は、' + determiner + head + 'を大切にしたい。' + TAIL)
    ref, = result.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert text[slice(*ref.reference_scalar_span)] == determiner + head
    assert result.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3'),)


@pytest.mark.parametrize('scope,relation', SCOPES)
@pytest.mark.parametrize('predicate', PREDICATES)
def test_scoped_focal_reference_keeps_both_clause_scopes_and_its_own_predicate(scope, relation, predicate):
    before = '僕にとって' + TARGET + 'が好きではなかったかもしれません。'
    prefix = '僕は' + scope + '、'
    focal = '僕が' + predicate + 'のは、その時間です。'
    result = generated(before + prefix + focal + TAIL,
                       '僕にとって、' + TARGET + 'が好きではなかったかもしれません。'
                       + prefix + 'その時間を' + predicate + '。' + TAIL)
    frame, = result.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')
    scope_info, = result.source_meaning.expression_scopes
    assert scope_info.relation == relation
    assert result.artifact_plan.duties[1].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'


@pytest.mark.parametrize('scope,relation', SCOPES)
def test_non_self_scope_does_not_take_the_focal_author(scope, relation):
    text = '私が望んでいるのは、' + TARGET + 'です。' + scope + '、僕が選びたくないのは、その時間です。' + TAIL
    result = generated(text, '私は、' + TARGET + 'を望んでいる。'
                       + scope + '、僕はその時間を選びたくない。' + TAIL)
    assert result.source_meaning.expression_scopes[0].relation == relation


@pytest.mark.parametrize('comma,gap', (('、', ' '), ('，', '\t'), (',', '\u3000')))
def test_source_offsets_survive_sentence_gaps_and_role_publicization(comma, gap):
    target = '同僚の秋山さんと静かに話す時間'
    first = '僕にとって大切なのは、' + target + 'です。'
    # A gap before a sentence must not change the original evidence coordinates.
    focal = '僕が大切にしたいのは' + comma + 'その時間です。'
    text = '🌱を見た。' + '\r\n\u3000' + first + gap + focal + TAIL
    result = generated(text, '🌱を見た。\n\n僕にとって、同僚と静かに話す時間が大切です。'
                       + '僕は、その時間を大切にしたい。' + TAIL)
    ref, = result.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert ref.reference_scalar_span == (text.index('その時間'), text.index('その時間') + len('その時間'))
    assert '秋山' not in result.artifact.piece_text


def test_bound_focal_mention_is_not_a_new_antecedent_for_a_later_evaluation():
    text = ('私が大切にしたいのは、' + TARGET + 'です。'
            + '私が選びたくないのは、その時間です。'
            + '私はその時間が苦手ではありません。' + TAIL)
    result = generated(text, '私は、' + TARGET + 'を大切にしたい。'
                       + '私は、その時間を選びたくない。'
                       + '私は、その時間が苦手ではありません。' + TAIL)
    refs = result.source_meaning.nominal_references
    assert len(refs) == 2
    assert [ref.antecedent_node_id for ref in refs] == ['piece:s1', 'piece:s1']
    assert refs[0].antecedent_scalar_span == refs[1].antecedent_scalar_span


@pytest.mark.parametrize('marker', ('ので', 'なら', 'ならば', 'けれど', 'けれども'))
def test_scope_and_focal_object_mentions_are_two_exact_ranges_of_one_referent(marker):
    first = '私にとって大切なのは、' + TARGET + 'です。'
    scope = 'その時間を続けられる' + marker
    text = first + scope + '、私が大切にしたいのは、その時間です。' + TAIL
    result = generated(text, '私にとって、' + TARGET + 'が大切です。'
                       + scope + '、私はその時間を大切にしたい。' + TAIL)
    refs = result.source_meaning.nominal_references
    assert len(refs) == 2
    assert refs[0].reference_scalar_span != refs[1].reference_scalar_span
    assert refs[0].antecedent_scalar_span == refs[1].antecedent_scalar_span
    assert all(ref.antecedent_node_id == 'piece:s1' for ref in refs)


def test_a_scoped_antecedent_keeps_its_condition_and_complete_object():
    scope = '私は無理なく続けられるなら、'
    text = scope + '私が大切にしたいのは、' + TARGET + 'です。私が選びたいのは、その時間です。' + TAIL
    result = generated(text, scope + TARGET + 'を大切にしたい。私は、その時間を選びたい。' + TAIL)
    ref, = result.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == TARGET
    assert ref.antecedent_scalar_span[0] > len(scope)
    assert result.source_meaning.expression_scopes[0].relation == 'SOURCE_EXPLICIT_CONDITION'


@pytest.mark.parametrize('prefix,object_text', (
    ('', 'その時間'),  # no antecedent
    ('空を見た。', 'その時間'),  # a context sentence is not an object
    ('私が大切にしたいのは、' + TARGET + 'です。私が選びたいのは、外を歩く時間です。', 'その時間'),
    ('空いた時間に出かけた。私が大切にしたいのは、' + TARGET + 'です。', 'その時間'),
    ('私が大切にしたいのは、' + TARGET + 'です。その時間は短い。別の時間に出かけた。', 'その時間'),
    ('私が大切にしたいのは、' + TARGET + 'です。', 'あの時間'),
    ('私が大切にしたいのは、' + TARGET + 'です。', 'その時間とこの時間'),
    ('私が大切にしたいのは、' + TARGET + 'です。', 'その時間より、外を歩く時間'),
    ('私が大切にしたいのは、' + TARGET + 'です。', 'その時間に話すこと'),
))
def test_missing_ambiguous_or_embedded_references_are_not_guessed(prefix, object_text):
    text = prefix + '私が望んでいるのは、' + object_text + 'です。' + TAIL
    assert outcome(text)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('reference_scalar', 'reference_utf8', 'antecedent', 'edge', 'removed'))
def test_modified_reference_metadata_cannot_author_the_artifact(mutation):
    text = '私が大切にしたいのは、' + TARGET + 'です。私が望んでいるのは、その時間です。' + TAIL
    _, result = outcome(text)
    assert result.status == EngineStatus.GENERATED
    meaning = result.source_meaning
    ref, = meaning.nominal_references
    if mutation == 'reference_scalar':
        changed = replace(ref, reference_scalar_span=(0, 4))
        meaning = replace(meaning, nominal_references=(changed,))
    elif mutation == 'reference_utf8':
        changed = replace(ref, reference_utf8_span=ref.reference_scalar_span)
        meaning = replace(meaning, nominal_references=(changed,))
    elif mutation == 'antecedent':
        changed = replace(ref, antecedent_node_id=ref.reference_node_id)
        meaning = replace(meaning, nominal_references=(changed,))
    elif mutation == 'edge':
        edges = tuple(e for e in meaning.graph.edges if e.relation != 'SOURCE_BOUND_NOMINAL_REFERENCE')
        meaning = replace(meaning, graph=replace(meaning.graph, edges=edges))
    else:
        meaning = replace(meaning, nominal_references=())
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, result.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('requested', ('quote', 'declaration'))
def test_reference_does_not_let_format_selection_detach_the_antecedent(requested):
    source, result = outcome('私が大切にしたいのは、' + TARGET + 'です。私が望んでいるのは、その時間です。' + TAIL)
    assert result.status == EngineStatus.GENERATED
    with pytest.raises(ValueError):
        generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
                                 tier='premium', requested_format=requested)


class Metrics:
    profile_id = 'focal-reference-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_complete_body_reaches_the_measured_layout(ratio):
    _, result = outcome('私にとって大切なのは、' + TARGET + 'です。'
                        + '私はまだ迷っているけれど、私が大切にしたいのは、その時間です。' + TAIL)
    assert result.status == EngineStatus.GENERATED
    candidate = result.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(result.artifact.body_blocks))] == list(result.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
