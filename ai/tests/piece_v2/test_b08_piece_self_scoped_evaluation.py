"""Keep the target of a same-author evaluation inside its written scope.

Public synthetic fixtures. A reason/condition/concession is not an evaluated
object, and a preference is not a wish. No speaker alias or new scope grammar.
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

TARGET = '一人で静かに手帳を開く時間'
TAIL = 'まだ、毎朝続けるかは決めていません。'
SCOPES = (
    ('落ち着いて考えられるので', 'ので', 'SOURCE_EXPLICIT_REASON'),
    ('無理なく続けられるなら', 'なら', 'SOURCE_EXPLICIT_CONDITION'),
    ('無理なく続けられるならば', 'ならば', 'SOURCE_EXPLICIT_CONDITION'),
    ('まだ迷っているけれど', 'けれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('まだ迷っているけれども', 'けれども', 'SOURCE_EXPLICIT_CONCESSION'),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'self-scoped-evaluation', '1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'self-scoped-evaluation', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, result


def generated(text, expected):
    source, result = outcome(text)
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    assert result.artifact.piece_text == expected
    meaning, plan = result.source_meaning, result.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert plan == compile_piece_artifact_plan(meaning)
    assert not plan.declaration_eligible
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end] == node.value.encode('utf-8')
    for frame in meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == result.artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled'] and not result.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return result


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('scope,marker,relation', SCOPES)
def test_both_word_orders_bind_the_inner_target_not_the_premise(speaker, scope, marker, relation):
    premise = speaker + 'は' + scope
    for expression in (speaker + 'が好きなのは、' + TARGET + 'です。',
                       speaker + 'は' + TARGET + 'が好きです。'):
        text = premise + '、' + expression + TAIL
        result = generated(text, premise + '、' + TARGET + 'が好きです。' + TAIL)
        frame = result.source_meaning.personal_evaluations[0]
        assert text[slice(*frame.scalar_parts[2])] == TARGET
        assert frame.scalar_parts[0][0] == len(premise) + 1
        assert frame.kind == 'PERSONAL_PREFERENCE'
        scope_info, = result.source_meaning.expression_scopes
        assert (scope_info.marker, scope_info.relation) == (marker, relation)
        assert text[slice(*scope_info.scope_scalar_span)] == premise
        assert text[slice(*scope_info.expression_scalar_span)] == expression
        assert result.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
        assert result.artifact_plan.block_node_ids == (tuple(n.node_id for n in result.source_meaning.graph.nodes),)


@pytest.mark.parametrize('predicate,polarity,time,commitment', (
    ('好きです', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('かなり苦手でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('苦手ではありません', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('苦手ではありませんでした', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('好きじゃなかったです', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('少し好きかもしれません', 'AFFIRMATIVE', 'NONPAST', 'POSSIBLE'),
    ('苦手ではないかもしれません', 'NEGATIVE', 'NONPAST', 'POSSIBLE'),
    ('苦手だったとは限りません', 'AFFIRMATIVE', 'PAST', 'NON_UNIVERSAL'),
    ('好きではなかったとは限らない', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
))
def test_finite_negation_time_degree_and_commitment_remain(predicate, polarity, time, commitment):
    prefix = '僕はまだ迷っているけれど、'
    result = generated(prefix + '僕は' + TARGET + 'が' + predicate + '。' + TAIL,
                       prefix + TARGET + 'が' + predicate + '。' + TAIL)
    frame = result.source_meaning.personal_evaluations[0]
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)


@pytest.mark.parametrize('relative,finite', (
    ('好きな', '好きです'), ('苦手だった', '苦手だった'),
    ('好きではない', '好きではない'), ('苦手ではなかった', '苦手ではなかった'),
    ('少し好きかもしれない', '少し好きかもしれない'),
    ('苦手だったとは限らない', '苦手だったとは限らない'),
))
def test_relative_evaluation_keeps_its_written_predicate(relative, finite):
    prefix = '私は無理なく続けられるなら、'
    generated(prefix + '私が' + relative + 'のは、' + TARGET + 'です。' + TAIL,
              prefix + TARGET + 'が' + finite + '。' + TAIL)


@pytest.mark.parametrize('base', ('大切', '大事', '重要', '必要'))
def test_explicit_value_viewpoint_is_not_omitted_or_replaced_by_a_wish(base):
    prefix = '私は落ち着いて考えられるので、'
    for expression in ('私にとって' + base + 'なのは、' + TARGET + 'です。',
                       '私にとって' + TARGET + 'が' + base + 'です。'):
        text = prefix + expression + TAIL
        result = generated(text, prefix + '私にとって' + TARGET + 'が' + base + 'です。' + TAIL)
        frame = result.source_meaning.personal_evaluations[0]
        assert (frame.construction, frame.kind) == ('にとって', 'PERSONAL_VALUE')
        assert text[slice(*frame.scalar_parts[2])] == TARGET


@pytest.mark.parametrize('target,head', ((TARGET, '時間'), ('机で紙を折ること', 'こと'),
                                        ('長く使い続けてきたもの', 'もの')))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_following_reference_uses_the_object_without_the_prior_scope(target, head, determiner):
    prefix = '僕はまだ迷っているけれど、僕は'
    reference = '僕は' + determiner + head + 'が苦手ではありません。'
    text = prefix + target + 'が好きです。' + reference + TAIL
    result = generated(text, '僕はまだ迷っているけれど、' + target + 'が好きです。僕は、'
                       + determiner + head + 'が苦手ではありません。' + TAIL)
    ref, = result.source_meaning.nominal_references
    assert ref.antecedent_scalar_span == (len(prefix), len(prefix) + len(target))
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert ref.reference_scalar_span == result.source_meaning.personal_evaluations[1].scalar_parts[2]
    assert text[slice(*ref.antecedent_scalar_span)].encode('utf-8') == text.encode('utf-8')[slice(*ref.antecedent_utf8_span)]


@pytest.mark.parametrize('comma,gap', (('、', ' '), ('，', '\t'), (',', '  ')))
def test_original_unicode_offsets_and_independent_context_remain(comma, gap):
    context = '🌱を眺めた。'
    prefix = 'おれは落ち着いて考えられるので'
    expression = 'おれは' + TARGET + 'が好きでした。'
    text = context + '\r\n\u3000' + prefix + comma + gap + expression + '\t' + TAIL
    result = generated(text, context + prefix + '、' + TARGET + 'が好きでした。' + TAIL)
    frame = result.source_meaning.personal_evaluations[0]
    assert frame.scalar_parts[0][0] == text.index(expression)
    assert text[slice(*frame.scalar_parts[2])] == TARGET
    assert result.source_meaning.expression_scopes[0].scope_scalar_span[0] == text.index(prefix)


def test_original_named_role_is_bound_before_publicization():
    target = '同僚の秋山さんと静かに話す時間'
    text = '僕はまだ迷っているけれど、僕が好きなのは、' + target + 'です。' + TAIL
    result = generated(text, '僕はまだ迷っているけれど、同僚と静かに話す時間が好きです。' + TAIL)
    frame = result.source_meaning.personal_evaluations[0]
    assert text[slice(*frame.scalar_parts[2])] == target
    assert result.source_meaning.role_bindings[0].name == '秋山さん'


@pytest.mark.parametrize('premise,speaker', (
    ('私はまだ迷っているけれど', '僕'),
    ('私はまだ迷っているけれど', 'わたし'),
    ('僕は彼が迷っているので', '僕'),
    ('僕はまだ迷っている、けれど', '僕'),
    ('僕は続けたいと聞いたので', '僕'),
    ('僕はまだ迷っているから', '僕'),
))
def test_unproven_author_or_scope_does_not_gain_an_inner_evaluation(premise, speaker):
    text = premise + '、' + speaker + 'が好きなのは、' + TARGET + 'です。' + TAIL
    assert outcome(text)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('target', 'speaker', 'predicate', 'utf8', 'scope', 'marker', 'relation'))
def test_changed_interpretation_cannot_drive_the_writer(mutation):
    text = '僕はまだ迷っているけれど、僕は' + TARGET + 'が好きです。' + TAIL
    result = generated(text, '僕はまだ迷っているけれど、' + TARGET + 'が好きです。' + TAIL)
    meaning = result.source_meaning
    frame = meaning.personal_evaluations[0]
    scope = meaning.expression_scopes[0]
    if mutation in ('target', 'speaker', 'predicate'):
        parts = list(frame.scalar_parts)
        i = {'speaker': 0, 'predicate': 1, 'target': 2}[mutation]
        parts[i] = (0, parts[i][1])
        meaning = replace(meaning, personal_evaluations=(replace(frame, scalar_parts=tuple(parts)),))
    elif mutation == 'utf8':
        meaning = replace(meaning, personal_evaluations=(replace(frame, utf8_parts=frame.scalar_parts),))
    else:
        changes = {'scope': {'scope_scalar_span': (1, scope.scope_scalar_span[1])},
                   'marker': {'marker': 'なら'}, 'relation': {'relation': 'SOURCE_EXPLICIT_CONDITION'}}
        meaning = replace(meaning, expression_scopes=(replace(scope, **changes[mutation]),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, result.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('requested', ('quote', 'declaration'))
def test_format_selection_cannot_detach_the_scope(requested):
    source, result = outcome('私は無理なく続けられるなら、私は' + TARGET + 'が好きです。' + TAIL)
    assert result.status == EngineStatus.GENERATED
    with pytest.raises(ValueError):
        generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
                                 tier='premium', requested_format=requested)


class Metrics:
    profile_id = 'self-scoped-evaluation-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_complete_scoped_body_enters_the_same_measured_image_path(ratio):
    result = generated('私は無理なく続けられるなら、私は' + TARGET + 'が好きです。' + TAIL,
                       '私は無理なく続けられるなら、' + TARGET + 'が好きです。' + TAIL)
    candidate = result.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(result.artifact.body_blocks))] == list(result.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
