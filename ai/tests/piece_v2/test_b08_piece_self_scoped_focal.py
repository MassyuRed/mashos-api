"""Source-written, same-author focal duties within one clause scope.

Fresh public synthetic fixtures, not recovered unpublished test evidence.
The scope, complete target, predicate and subsequent reservation stay intact.
No inferred speaker aliases, reported voice or cross-sentence topic omission.
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
    ('無理なく続けられるなら', 'なら', 'SOURCE_EXPLICIT_CONDITION'),
    ('無理なく続けられるならば', 'ならば', 'SOURCE_EXPLICIT_CONDITION'),
    ('まだ迷っているけれど', 'けれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('まだ迷っているけれども', 'けれども', 'SOURCE_EXPLICIT_CONCESSION'),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'self-scoped-focal', '1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'self-scoped-focal', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, result


def generated(text, expected):
    source, result = outcome(text)
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    assert result.artifact.piece_text == expected
    meaning, plan = result.source_meaning, result.artifact_plan
    raw = text.encode('utf-8')
    assert meaning.envelope.raw_utf8 == raw
    assert plan == compile_piece_artifact_plan(meaning)
    ids = tuple(node.node_id for node in meaning.graph.nodes)
    assert plan.block_node_ids == (ids,)
    assert not plan.declaration_eligible
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert raw[evidence.utf8_start:evidence.utf8_end] == node.value.encode('utf-8')
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == raw[slice(*utf8)]
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == result.artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled'] and not result.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return result


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('scope,marker,relation', SCOPES)
def test_the_written_same_author_is_retained_once(speaker, scope, marker, relation):
    premise = speaker + 'は' + scope
    focal = speaker + 'が大切にしたいのは、' + TARGET + 'です。'
    result = generated(premise + '、' + focal + TAIL,
                       premise + '、' + TARGET + 'を大切にしたい。' + TAIL)
    assert len(result.source_meaning.expression_scopes) == 1
    bound = result.source_meaning.expression_scopes[0]
    text = result.source_meaning.envelope.raw_utf8.decode('utf-8')
    assert (bound.marker, bound.relation) == (marker, relation)
    assert text[slice(*bound.scope_scalar_span)] == premise
    assert text[slice(*bound.expression_scalar_span)] == focal
    assert result.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'


@pytest.mark.parametrize('predicate', (
    '大切にしたい', '大切にしている', '大切にしたくない',
    '望んでいる', '望んでいない', '選びたい', '選びたくない',
))
@pytest.mark.parametrize('copula', ('です', 'だ'))
def test_the_complete_predicate_and_its_negation_remain_written(predicate, copula):
    premise = '僕は落ち着いて考えられるので'
    generated(premise + '、僕が' + predicate + 'のは、' + TARGET + copula + '。' + TAIL,
              premise + '、' + TARGET + 'を' + predicate + '。' + TAIL)


@pytest.mark.parametrize('scope,marker,relation', SCOPES)
def test_existing_context_and_reservation_are_not_replaced(scope, marker, relation):
    context = '僕にとって予定を詰めすぎないことが大切です。'
    result = generated(context + '僕は' + scope + '、僕が選びたいのは、' + TARGET + 'です。' + TAIL,
                       '僕にとって、予定を詰めすぎないことが大切です。僕は' + scope
                       + '、' + TARGET + 'を選びたい。' + TAIL)
    assert [d.operation for d in result.artifact_plan.duties] == [
        'SOURCE_PERSONAL_EVALUATION', 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON',
        'KEEP_COMPLETE_SOURCE_CONTEXT']


@pytest.mark.parametrize('target,head', (
    (TARGET, '時間'), ('自分の順番で紙を折ること', 'こと'), ('長く使い続けてきたもの', 'もの'),
))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_reference_binds_only_the_whole_scoped_object(target, head, determiner):
    prefix = '私はまだ迷っているけれど、私が選びたいのは、'
    following = '私は' + determiner + head + 'が苦手ではないかもしれません。'
    result = generated(prefix + target + 'です。' + following + TAIL,
                       '私はまだ迷っているけれど、' + target + 'を選びたい。私は、'
                       + determiner + head + 'が苦手ではないかもしれません。' + TAIL)
    ref, = result.source_meaning.nominal_references
    assert ref.antecedent_scalar_span == (len(prefix), len(prefix) + len(target))
    frame, = result.source_meaning.personal_evaluations
    assert ref.reference_scalar_span == frame.scalar_parts[2]
    assert (frame.polarity, frame.commitment) == ('NEGATIVE', 'POSSIBLE')


@pytest.mark.parametrize('comma', ('、', '，', ','))
@pytest.mark.parametrize('gap', (' ', '\t'))
def test_original_unicode_and_punctuation_are_the_binding_coordinates(comma, gap):
    context = '🌱を眺めた。'
    premise = 'ぼくは' + comma + '落ち着いて考えられるので'
    focal = 'ぼくが選びたくないのは、慌てて結論を決めることです。'
    text = context + '\r\n\u3000' + premise + comma + gap + focal + '  ' + TAIL
    result = generated(text, context + premise + '、慌てて結論を決めることを選びたくない。' + TAIL)
    bound, = result.source_meaning.expression_scopes
    assert bound.scope_scalar_span[0] == text.index(premise)
    assert bound.expression_scalar_span[0] == text.index(focal)


def test_role_publicization_keeps_original_object_and_subject_evidence():
    target = '同僚の秋山さんと静かに話す時間'
    prefix = '俺はまだ迷っているけれど、俺が望んでいるのは、'
    result = generated(prefix + target + 'です。俺はその時間が好きでした。' + TAIL,
                       '俺はまだ迷っているけれど、同僚と静かに話す時間を望んでいる。'
                       '俺は、その時間が好きでした。' + TAIL)
    ref, = result.source_meaning.nominal_references
    text = result.source_meaning.envelope.raw_utf8.decode('utf-8')
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert result.source_meaning.role_bindings[0].name == '秋山さん'


@pytest.mark.parametrize('premise,speaker', (
    ('私はまだ迷っているけれど', '僕'),
    ('私はまだ迷っているけれど', 'わたし'),
    ('先輩はまだ迷っているけれど', '私'),
    ('私は先輩が迷っているけれど', '私'),
    ('私は先輩は迷っているけれど', '私'),
    ('私は先輩も迷っているけれど', '私'),
    ('私は休みたいと聞いたので', '私'),
    ('私は休みたいって言ったので', '私'),
    ('私は迷っていると、僕は言ったけれど', '私'),
    ('私は迷っている、けれど', '私'),
))
def test_unproved_self_scope_does_not_gain_the_omission(premise, speaker):
    text = premise + '、' + speaker + 'が選びたいのは、' + TARGET + 'です。' + TAIL
    _, result = outcome(text)
    # A non-self premise retains the already-admitted, explicit focal author.
    if premise.startswith('先輩は'):
        assert result.status == EngineStatus.GENERATED
        assert '、私は' + TARGET + 'を選びたい。' in result.artifact.piece_text
    else:
        assert result.status == EngineStatus.UNAVAILABLE


def test_declining_an_ambiguous_edit_does_not_remove_existing_context():
    context = '私にとって予定を詰めすぎないことが大切です。'
    sentence = '私は先輩が迷っているけれど、私が選びたいのは、' + TARGET + 'です。'
    _, result = outcome(context + sentence + TAIL)
    assert result.status == EngineStatus.GENERATED
    assert result.artifact.piece_text == '私にとって、予定を詰めすぎないことが大切です。' + sentence + TAIL
    assert result.artifact_plan.duties[1].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'


@pytest.mark.parametrize('mutation', ('scope', 'expression', 'utf8', 'relation', 'reference'))
def test_tampered_source_scope_or_reference_cannot_author_the_body(mutation):
    text = '私はまだ迷っているけれど、私が選びたいのは、' + TARGET + 'です。私はその時間が好きです。' + TAIL
    _, result = outcome(text)
    assert result.status == EngineStatus.GENERATED
    meaning = result.source_meaning
    if mutation == 'reference':
        ref, = meaning.nominal_references
        meaning = replace(meaning, nominal_references=(replace(
            ref, antecedent_scalar_span=(0, ref.antecedent_scalar_span[1])),))
    else:
        scope, = meaning.expression_scopes
        changes = {
            'scope': {'scope_scalar_span': (1, scope.scope_scalar_span[1])},
            'expression': {'expression_scalar_span': (scope.expression_scalar_span[0] + 1,
                                                      scope.expression_scalar_span[1])},
            'utf8': {'expression_utf8_span': scope.expression_scalar_span},
            'relation': {'relation': 'SOURCE_EXPLICIT_REASON'},
        }
        meaning = replace(meaning, expression_scopes=(replace(scope, **changes[mutation]),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, result.artifact_plan, tier='free', requested_format=None)


class Metrics:
    profile_id = 'self-scoped-focal-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_the_canonical_body_is_the_existing_image_path_input(ratio):
    _, result = outcome('私はまだ迷っているけれど、私が選びたいのは、' + TARGET + 'です。' + TAIL)
    assert result.status == EngineStatus.GENERATED
    candidate = result.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(result.artifact.body_blocks))] == list(result.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    for requested in ('quote', 'declaration'):
        source, _ = outcome('私はまだ迷っているけれど、私が選びたいのは、' + TARGET + 'です。' + TAIL)
        with pytest.raises(ValueError):
            generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
                                     tier='premium', requested_format=requested)
