"""Fullwidth clause gaps preserve original Piece scope and canonical meaning.

Synthetic, code-disabled Piece component regression. This calls the actual
source/plan/writer, not an emulated engine, API, saved-input or native route.
"""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_source import _SCOPED_EXPRESSION
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, generate_piece_artifact, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

SCOPES = (
    ('気持ちが落ち着かなかったので', 'SOURCE_EXPLICIT_REASON', 'ので'),
    ('予定が合うなら', 'SOURCE_EXPLICIT_CONDITION', 'なら'),
    ('予定が合うならば', 'SOURCE_EXPLICIT_CONDITION', 'ならば'),
    ('まだ迷っていたけれど', 'SOURCE_EXPLICIT_CONCESSION', 'けれど'),
    ('まだ迷っていたけれども', 'SOURCE_EXPLICIT_CONCESSION', 'けれども'),
)
# Every intention is already supported without the newly admitted gap.
# Explicit expected text also guards against both variants losing meaning.
EXPRESSIONS = (
    ('私は静かに考える時間を望んでいなかったかもしれない。',
     '私は静かに考える時間を望んでいなかったかもしれない。'),
    ('私は自分で答えを選ぶことを大切にしたくないです。',
     '私は自分で答えを選ぶことを大切にしたくないです。'),
    ('私が大切にしたくなかったのは、自分で答えを選ぶことです。',
     '私は自分で答えを選ぶことを大切にしたくなかった。'),
    ('私にとって静かに考える時間が必要だったとは限らない。',
     '私にとって、静かに考える時間が必要だったとは限らない。'),
    ('私は静かに考える時間が好きではありませんでした。',
     '私は、静かに考える時間が好きではありませんでした。'),
)


def run(text, *, stage='normal_observation', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-scope-gap', 'v1',
                                 text, source_stage=stage)
    return source, generate_piece_artifact(PieceGenerationRequest(
        'synthetic-scope-gap', source, source.owner_id, source.saved_input_id,
        source.source_version, tier='premium', requested_format=requested_format))


def checked(text, *, stage='normal_observation'):
    source, out = run(text, stage=stage)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert source.original_text == text
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert meaning.envelope.raw_sha256 == hashlib.sha256(text.encode('utf-8')).hexdigest()
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode('utf-8')[ev.utf8_start:ev.utf8_end].decode('utf-8') == node.value
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    for frame in meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    frozen = deepcopy((asdict(meaning), asdict(plan)))
    assert realize_piece_artifact(meaning, plan, tier='premium', requested_format=None) == artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    candidate = artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(artifact.piece_text.encode('utf-8')).hexdigest()
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert artifact.eligible_formats == ('short_essay',)
    assert not plan.declaration_eligible
    return out


@pytest.mark.parametrize('scope,relation,marker', SCOPES)
@pytest.mark.parametrize('expression,visible', EXPRESSIONS)
@pytest.mark.parametrize('comma', ('、', '，', ','))
def test_fullwidth_gap_keeps_complete_scope_predicate_and_original_coordinates(
        scope, relation, marker, expression, visible, comma):
    plain = scope + comma + expression
    raw = scope + comma + '\u3000' + expression
    expected = checked(plain)
    actual = checked(raw)
    assert actual.artifact == expected.artifact
    assert actual.artifact.piece_text == scope + '、' + visible
    bound, = actual.source_meaning.expression_scopes
    assert (bound.relation, bound.marker) == (relation, marker)
    assert raw[slice(*bound.scope_scalar_span)] == scope
    assert raw[slice(*bound.expression_scalar_span)] == expression
    assert bound.expression_scalar_span[0] == len(scope + comma + '\u3000')
    assert bound.expression_utf8_span[0] == len((scope + comma + '\u3000').encode('utf-8'))
    for fmt in ('quote', 'declaration'):
        refused = run(raw, requested_format=fmt)[1]
        assert refused.status == EngineStatus.UNAVAILABLE
        assert refused.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('gap', ('', ' ', '\t', '\u3000\u3000', ' \t\u3000 \t'))
def test_horizontal_gaps_have_one_body_without_normalizing_the_source(gap):
    expression = EXPRESSIONS[0][0]
    raw = '予定が合うなら、' + gap + expression
    actual = checked(raw)
    assert actual.artifact == checked('予定が合うなら、' + expression).artifact


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('stage', ('normal_observation', 'pre_question_observation'))
def test_same_explicit_scope_author_keeps_negation_and_tense(speaker, stage):
    raw = speaker + 'はまだ迷っていたけれど、\u3000' + speaker + 'は静かに考える時間を望んでいませんでした。'
    actual = checked(raw, stage=stage)
    assert actual.artifact.piece_text == speaker + 'はまだ迷っていたけれど、静かに考える時間を望んでいませんでした。'
    assert actual.artifact == checked(raw.replace('、\u3000', '、'), stage=stage).artifact


@pytest.mark.parametrize('raw', (
    '僕は静かに考える時間を大切にしていた。その時間なら、\u3000僕は答えを急がずに待ちたい。',
    '僕は静かに考える時間を大切にしていた。まだ迷っていたけれど、\u3000僕はその時間を望んでいなかったかもしれない。',
    '僕は静かに考える時間を大切にしていた。僕は自分で答えを選ぶことを望んでいた。その時間とこのことなら、\u3000僕は焦らずに続けたい。',
    '🌱を見た。\r\n\u3000まだ迷っていたけれど、\u3000僕は同僚の秋山さんと話す時間を望んでいなかったかもしれない。\t僕はその時間が好きではありませんでした。',
))
def test_references_and_role_projection_keep_the_original_scope_boundary(raw):
    actual = checked(raw)
    assert actual.artifact == checked(raw.replace('、\u3000', '、')).artifact
    assert actual.source_meaning.nominal_references
    assert '秋山' not in actual.artifact.piece_text
    scope, = actual.source_meaning.expression_scopes
    assert raw[slice(*scope.expression_scalar_span)].startswith('僕は')


@pytest.mark.parametrize('gap', ('\n', '\r', '\r\n', '\v', '\f', '\u00a0', '\u2028', '\u200b', '、\u3000'))
def test_other_separators_do_not_gain_admission_or_bridge_an_unfinished_line(gap):
    raw = '予定が合うなら、' + gap + EXPRESSIONS[0][0]
    assert _SCOPED_EXPRESSION.fullmatch(raw) is None
    out = run(raw)[1]
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('expression', (
    '静かに考える時間を望んでいなかった。',
    '友人は静かに考える時間を望んでいなかった。',
    '私はその時間を望んでいなかった。',
    '私は静かに考える時間を望んでいましたと聞いた。',
    '私は静かに考える時間を望んでいなかったかもしれないとは限らない。',
))
def test_spacing_does_not_infer_subject_reference_report_or_stacked_modality(expression):
    raw = '予定が合うなら、\u3000' + expression
    out = run(raw)[1]
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('mutation', ('scope', 'coordinates', 'relation', 'declaration'))
def test_source_validation_still_precedes_realization(mutation):
    raw = '予定が合うなら、\u3000' + EXPRESSIONS[0][0]
    out = checked(raw)
    meaning, plan = out.source_meaning, out.artifact_plan
    scope, = meaning.expression_scopes
    if mutation == 'scope':
        meaning = replace(meaning, expression_scopes=())
    elif mutation == 'coordinates':
        meaning = replace(meaning, expression_scopes=(replace(scope,
            expression_scalar_span=(scope.expression_scalar_span[0] - 1, scope.expression_scalar_span[1])),))
    elif mutation == 'relation':
        meaning = replace(meaning, expression_scopes=(replace(scope, relation='SOURCE_EXPLICIT_REASON'),))
    else:
        plan = replace(plan, declaration_eligible=True)
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='premium', requested_format=None)


class Metrics:
    profile_id = 'scope-gap-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -.8 * font_px, width, .2 * font_px)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_canonical_body_reaches_existing_layout_without_text_loss(ratio):
    out = checked('予定が合うなら、\u3000' + EXPRESSIONS[0][0])
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
