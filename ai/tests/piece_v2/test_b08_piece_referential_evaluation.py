"""Source-bound evaluation arguments use the existing nominal-reference owner.

All fixtures are synthetic. No nearest-mention guess or new source is admitted.
These are disabled B8/B9 technical checks, not native/product acceptance.
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
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
TARGET = '窓辺で草花を眺める時間'
TAIL = 'まだ、毎日予定を空けられるとは限らない。'


def run(text, **kwargs):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-target', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-target-evaluation', source, source.owner_id,
        source.saved_input_id, source.source_version, **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


def case_text(speaker='僕', word_order='finite', demonstrative='その'):
    first = speaker + 'にとって' + TARGET + 'が大切です。'
    second = (speaker + 'は' + demonstrative + '時間が好きです。' if word_order == 'finite'
              else speaker + 'が好きなのは、' + demonstrative + '時間です。')
    return first + second + TAIL


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('word_order', ('finite', 'focus'))
@pytest.mark.parametrize('demonstrative', ('その', 'この'))
def test_same_referent_can_receive_its_own_explicit_evaluation(speaker, word_order, demonstrative):
    text = case_text(speaker, word_order, demonstrative)
    expected = speaker + 'にとって、' + TARGET + 'が大切です。' + speaker + 'は、' + demonstrative + '時間が好きです。' + TAIL
    out = generated(text)
    meaning = out.source_meaning
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert meaning.envelope.raw_utf8.decode() == text
    first, second = meaning.personal_evaluations
    ref, = meaning.nominal_references
    assert ref.antecedent_node_id == first.node_id and ref.reference_node_id == second.node_id
    assert ref.antecedent_scalar_span == first.scalar_parts[2]
    assert ref.reference_scalar_span == second.scalar_parts[2]
    assert text[slice(*ref.reference_scalar_span)] == demonstrative + '時間'
    assert tuple(d.operation for d in out.artifact_plan.duties) == (
        'SOURCE_PERSONAL_EVALUATION', 'SOURCE_PERSONAL_EVALUATION', 'KEEP_COMPLETE_SOURCE_CONTEXT')
    for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                         (ref.reference_scalar_span, ref.reference_utf8_span)):
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    edge, = (e for e in meaning.graph.edges if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE')
    assert edge.source_node_id == second.node_id and edge.target_node_id == first.node_id
    assert edge.evidence_ids == (meaning.graph.nodes[0].evidence_ids[0], meaning.graph.nodes[1].evidence_ids[0])
    candidate = generate_piece_candidate(PieceSourceSnapshot('synthetic-owner', 'synthetic-target', 'v1', text),
                                         authenticated_owner_id='synthetic-owner')
    assert candidate == out.artifact.as_candidate()
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('ending,polarity,time,commitment', (
    ('です', 'AFFIRMATIVE', 'NONPAST', 'ASSERTED'),
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('だったかもしれない', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('とは限らない', 'AFFIRMATIVE', 'NONPAST', 'NON_UNIVERSAL'),
    ('じゃなかったとは限らない', 'NEGATIVE', 'PAST', 'NON_UNIVERSAL'),
))
def test_reference_does_not_copy_antecedent_evaluation_or_commitment(ending, polarity, time, commitment):
    text = '  私にとって🌱を眺めて過ごす時間が大切です。\r\n私にとってその時間が必要' + ending + '。' + TAIL + '  '
    out = generated(text)
    second = out.source_meaning.personal_evaluations[1]
    assert (second.polarity, second.temporal_scope, second.commitment) == (polarity, time, commitment)
    assert text[slice(*second.scalar_parts[1])] == '必要' + ending
    assert out.artifact.piece_text == '私にとって、🌱を眺めて過ごす時間が大切です。私にとって、その時間が必要' + ending + '。' + TAIL
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('scope', ('空が明るいなら、', '空が明るいので、', '空が明るいけれど、'))
def test_written_scope_belongs_to_the_referencing_evaluation(scope):
    text = '私にとって' + TARGET + 'が大切です。' + scope + '私にとってその時間が必要かもしれない。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == '私にとって、' + TARGET + 'が大切です。' + scope + '私にとって、その時間が必要かもしれない。' + TAIL
    frame = out.source_meaning.personal_evaluations[1]
    ref, = out.source_meaning.nominal_references
    relation, = out.source_meaning.expression_scopes
    assert frame.node_id == ref.reference_node_id == relation.node_id
    assert relation.expression_scalar_span[0] <= ref.reference_scalar_span[0]
    assert ref.reference_scalar_span[1] <= relation.expression_scalar_span[1]
    assert out.artifact_plan.duties[1].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'


@pytest.mark.parametrize('target,head', (
    ('窓辺で草花を眺める時間', '時間'),
    ('自分の手で紙を折ること', 'こと'),
    ('長く手元で使ってきたもの', 'もの'),
))
def test_references_do_not_become_new_competing_antecedents(target, head):
    text = '私にとって' + target + 'が大切です。私はその' + head + 'が好きです。私にとってこの' + head + 'が必要かもしれない。' + TAIL
    out = generated(text)
    assert len(out.source_meaning.personal_evaluations) == 3
    assert len(out.source_meaning.nominal_references) == 2
    assert all(ref.antecedent_node_id == 'piece:s1' for ref in out.source_meaning.nominal_references)
    assert out.artifact.piece_text == '私にとって、' + target + 'が大切です。私は、その' + head + 'が好きです。私にとって、この' + head + 'が必要かもしれない。' + TAIL


def test_scope_and_argument_mentions_are_both_bound_in_source_order():
    text = '私にとって' + TARGET + 'が大切です。その時間が取れるなら、私にとってその時間が必要かもしれない。' + TAIL
    out = generated(text)
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert refs[0].reference_scalar_span[1] < refs[1].reference_scalar_span[0]
    assert all(ref.antecedent_node_id == 'piece:s1' and ref.reference_node_id == 'piece:s2' for ref in refs)
    assert out.artifact.piece_text == '私にとって、' + TARGET + 'が大切です。その時間が取れるなら、私にとって、その時間が必要かもしれない。' + TAIL


def test_original_names_are_publicized_only_after_the_reference_is_bound():
    text = '僕にとって友人の林さんの同僚の井上さんと落ち着いて話す時間が大切です。僕はその時間が好きです。まだ、会う日は決めていない。'
    out = generated(text)
    assert out.artifact.piece_text == '僕にとって、友人の同僚と落ち着いて話す時間が大切です。僕は、その時間が好きです。まだ、会う日は決めていない。'
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == '友人の林さんの同僚の井上さんと落ち着いて話す時間'


@pytest.mark.parametrize('text', (
    '私はその時間が好きです。',
    '私が好きなのは、その時間です。',
    '私はその時間が好きです。私にとって窓辺で草花を眺める時間が大切です。',
    '私にとって窓辺で草花を眺める時間が大切です。私はそのことが好きです。',
    '私にとって窓辺で草花を眺める時間が大切です。私にとって街をゆっくり歩く時間が必要です。私はその時間が好きです。',
    '私にとって窓辺で草花を眺める時間が大切です。友人は庭で過ごす時間を取った。私はその時間が好きです。',
    '私にとって窓辺で草花を眺める時間が大切です。私はその時間帯が好きです。',
    '私にとって窓辺で草花を眺める時間が大切です。私はその時間を確保することが好きです。',
    '私にとって窓辺で草花を眺める時間が大切です。私はそれが好きです。',
))
def test_unresolved_or_unmodelled_reference_evaluation_is_not_licensed(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('second', (
    '私はその時間は好きです。',
    '私はその時間が好きだと友人が言った。',
    '私はその時間が好きかもしれないとは限らない。',
))
def test_existing_contrast_report_and_nested_modal_remain_complete_context(second):
    # These were already generated context, not self-evaluation frames. Preserve
    # them, without changing a contrast, reporter or modal into the author's fact.
    text = '私にとって' + TARGET + 'が大切です。' + second
    out = generated(text)
    assert out.artifact.piece_text == '私にとって、' + TARGET + 'が大切です。' + second
    assert len(out.source_meaning.personal_evaluations) == 1
    assert out.artifact_plan.duties[1].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'


@pytest.mark.parametrize('mutation', ('drop_ref', 'target_span', 'antecedent', 'edge', 'polarity', 'drop_duty', 'split', 'reorder'))
def test_existing_author_recomputes_reference_and_evaluation_before_realization(mutation):
    out = generated(case_text())
    meaning, plan = out.source_meaning, out.artifact_plan
    ref, = meaning.nominal_references
    if mutation == 'drop_ref': meaning = replace(meaning, nominal_references=())
    if mutation == 'target_span': meaning = replace(meaning, nominal_references=(replace(ref, reference_scalar_span=(0, 2)),))
    if mutation == 'antecedent': meaning = replace(meaning, nominal_references=(replace(ref, antecedent_node_id=ref.reference_node_id),))
    if mutation == 'edge': meaning = replace(meaning, graph=replace(meaning.graph, edges=tuple(e for e in meaning.graph.edges if e.relation != 'SOURCE_BOUND_NOMINAL_REFERENCE')))
    if mutation == 'polarity': meaning = replace(meaning, personal_evaluations=(meaning.personal_evaluations[0], replace(meaning.personal_evaluations[1], polarity='NEGATIVE')))
    if mutation == 'drop_duty': plan = replace(plan, duties=plan.duties[:-1])
    if mutation == 'split': plan = replace(plan, block_node_ids=tuple((n.node_id,) for n in meaning.graph.nodes))
    if mutation == 'reorder': plan = replace(plan, block_node_ids=(tuple(n.node_id for n in reversed(meaning.graph.nodes)),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier,fmt', (('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay')))
def test_existing_tiers_use_one_body(tier, fmt):
    assert generated(case_text(), tier=tier, requested_format=fmt).artifact.piece_text == generated(case_text()).artifact.piece_text


@pytest.mark.parametrize('tier,fmt', (('free', 'short_essay'), ('plus', 'short_essay'), ('premium', 'quote'), ('premium', 'declaration')))
def test_referent_cannot_be_detached_to_grant_another_format(tier, fmt):
    out = run(case_text(), tier=tier, requested_format=fmt)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_existing_b9_consumes_the_entire_referential_evaluation(ratio):
    class Metrics:
        profile_id = 'synthetic-referential-evaluation-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    candidate = generated(case_text()).artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(row['text'] for row in layout['lines']) == candidate['piece_text']
