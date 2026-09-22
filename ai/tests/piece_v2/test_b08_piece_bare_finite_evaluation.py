"""Bare finite evaluations use the existing source/plan/author path.

Synthetic source sentences, not supplied user records or native acceptance.
No copula, omitted speaker, causal relation or commitment is invented.
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

TARGET = '窓辺で鉢植えを眺めて過ごす時間'
OTHER = '公園で小鳥の声を聞く時間'
TAIL = 'まだ、毎朝続けられるとは限らない。'
SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
FORMS = (('は', '好き'), ('は', '苦手')) + tuple(
    ('にとって', base) for base in ('大切', '大事', '重要', '必要', '好き', '苦手'))


def run(text, *, tier='free', requested_format=None, **changes):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-bare-evaluation', 'v1', text)
    actual = replace(source, **changes) if changes else source
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-bare-evaluation', actual, source.owner_id, source.saved_input_id,
        source.source_version, tier, requested_format))
    return source, out


def generated(text, **kwargs):
    source, out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert out.source_meaning.envelope.raw_sha256 == hashlib.sha256(text.encode()).hexdigest()
    plan = out.artifact_plan
    assert plan == compile_piece_artifact_plan(out.source_meaning)
    covered = tuple(n for block in plan.block_node_ids for n in block)
    assert sorted(covered) == sorted(n.node_id for n in out.source_meaning.graph.nodes)
    assert len(covered) == len(out.source_meaning.graph.nodes)
    for node, ev in zip(out.source_meaning.graph.nodes, out.source_meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    snapshot = asdict(out.source_meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, **kwargs)
    assert candidate == out.artifact.as_candidate()
    assert snapshot == (asdict(out.source_meaning), asdict(plan))
    body = out.artifact.piece_text
    assert candidate['piece_text_hash'] == hashlib.sha256(body.encode()).hexdigest()
    assert validate_piece_text_binding(candidate['content_payload'], body,
                                       candidate['piece_text_hash']) == body
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert not out.automatic_progression
    return out


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('construction,base', FORMS)
def test_complete_bare_finite_clause_has_source_owned_viewpoint_and_predicate(speaker, construction, base):
    text = speaker + construction + TARGET + 'が' + base + '。' + TAIL
    out = generated(text)
    expected = speaker + construction + '、' + TARGET + 'が' + base + '。' + TAIL
    assert out.artifact.piece_text == expected
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2'),)
    assert not out.artifact_plan.declaration_eligible
    frame, = out.source_meaning.personal_evaluations
    assert frame.construction == construction
    assert frame.copula == ''
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('AFFIRMATIVE', 'NONPAST', 'ASSERTED')
    assert [text[slice(*p)] for p in frame.scalar_parts] == [speaker, base, TARGET]
    assert out.artifact_plan.duties[0].operation == 'SOURCE_PERSONAL_EVALUATION'
    assert out.artifact_plan.duties[1].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'


@pytest.mark.parametrize('marker', ('ので', 'なら', 'ならば', 'けれど', 'けれども'))
@pytest.mark.parametrize('construction,base', (('は', '好き'), ('にとって', '必要')))
def test_scope_stays_attached_without_adding_a_finite_copula(marker, construction, base):
    premise = '予定が空く' + marker
    target = '🌱を窓辺で眺めて過ごす時間'
    text = ' \t' + premise + '、僕' + construction + target + 'が' + base + '。\r\n' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == premise + '、僕' + construction + '、' + target + 'が' + base + '。' + TAIL
    frame, = out.source_meaning.personal_evaluations
    scope, = out.source_meaning.expression_scopes
    assert scope.marker == marker
    assert text[slice(*scope.scope_scalar_span)] == premise
    assert text[slice(*scope.expression_scalar_span)] == '僕' + construction + target + 'が' + base + '。'
    for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
        assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('head,antecedent,other', (
    ('時間', TARGET, OTHER),
    ('こと', '自分の手で形を確かめること', '遠くから全体を眺めること'),
    ('もの', '手元で長く使ってきたもの', '棚に並べて眺めるもの'),
))
@pytest.mark.parametrize('position', ('whole', 'left', 'right'))
def test_existing_reference_and_comparison_meaning_are_used_not_replaced(head, antecedent, other, position):
    mention = 'その' + head
    target = mention if position == 'whole' else (
        mention + 'より、' + other if position == 'left' else other + 'より、' + mention)
    first = '僕が大切にしたいのは、' + antecedent + 'です。'
    text = first + '  僕は' + target + 'が好き。' + TAIL
    out = generated(text)
    # Reuse the existing proven whole-reference omission only. Comparison
    # operands must not be mistaken for the complete evaluation target.
    prefix = '' if position == 'whole' else '僕は、'
    assert out.artifact.piece_text == '僕は、' + antecedent + 'を大切にしたい。' + prefix + target + 'が好き。' + TAIL
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == 'piece:s1' and ref.reference_node_id == 'piece:s2'
    assert text[slice(*ref.antecedent_scalar_span)] == antecedent
    assert text[slice(*ref.reference_scalar_span)] == mention
    frame, = out.source_meaning.personal_evaluations
    assert text[slice(*frame.scalar_parts[2])] == target
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3'),)
    assert out.artifact.eligible_formats == ('short_essay',)


def test_named_role_chain_and_following_bare_comparison_keep_every_relationship():
    first = '僕にとって友人の高橋さんの同僚の伊藤さんと落ち着いて話す時間が大切。'
    text = first + '僕はその時間より、' + OTHER + 'が好き。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == ('僕にとって、友人の同僚と落ち着いて話す時間が大切。'
        + '僕は、その時間より、' + OTHER + 'が好き。' + TAIL)
    assert len(out.source_meaning.personal_evaluations) == 2
    assert len(out.source_meaning.nominal_references) == 1


@pytest.mark.parametrize('text', (
    '友人は' + TARGET + 'が好き。',
    TARGET + 'が好き。',
    '私は' + TARGET + 'が必要。',
    '私は' + TARGET + 'は好き。',
    '私は' + TARGET + 'も好き。',
    '私は' + TARGET + 'が好きな。',
    '私は' + TARGET + 'が好きと思う。',
    '私は' + TARGET + 'が好きだと聞いた。',
    '私は' + TARGET + 'が好きではないと思う。',
    '私は' + TARGET + 'が好きかもしれないとは限らない。',
    '私はその時間が好き。',
    '僕が好きなのは、' + TARGET + '。',
    '私は高橋さんと落ち着いて話す時間が好き。',
    '私は「' + TARGET + 'が好き」と聞いた。',
))
def test_no_guessed_speaker_copula_reference_or_outer_commitment(text):
    _, out = run(text + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('change', ('copula', 'polarity', 'time', 'speaker', 'utf8', 'drop_duty'))
def test_source_and_plan_validation_still_reject_fabricated_meaning(change):
    out = generated('僕は' + TARGET + 'が好き。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    frame, = meaning.personal_evaluations
    if change == 'drop_duty':
        plan = replace(plan, duties=plan.duties[:-1])
    else:
        fields = {
            'copula': {'copula': 'です'}, 'polarity': {'polarity': 'NEGATIVE'},
            'time': {'temporal_scope': 'PAST'},
            'speaker': {'scalar_parts': ((1, 2), *frame.scalar_parts[1:])},
            'utf8': {'utf8_parts': ((1, 3), *frame.utf8_parts[1:])},
        }[change]
        meaning = replace(meaning, personal_evaluations=(replace(frame, **fields),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('changes,reason', (
    ({'owner_id': 'another-owner'}, 'source_owner_mismatch'),
    ({'saved_input_id': 'another-source'}, 'saved_input_binding_mismatch'),
    ({'source_version': 'v2'}, 'source_version_binding_mismatch'),
    ({'source_role': 'supplemental'}, 'source_role_or_stage_not_yet_supported'),
    ({'source_stage': 'refined'}, 'source_role_or_stage_not_yet_supported'),
))
def test_bare_predicate_cannot_bypass_saved_source_binding(changes, reason):
    _, out = run('僕は' + TARGET + 'が好き。' + TAIL, **changes)
    assert out.status == EngineStatus.UNAVAILABLE and out.reason_codes == (reason,)
    assert out.artifact is None


@pytest.mark.parametrize('tier,requested', (('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay')))
def test_existing_tiers_keep_the_same_original_bare_register(tier, requested):
    out = generated('僕は' + TARGET + 'が好き。' + TAIL, tier=tier, requested_format=requested)
    assert out.artifact.piece_text == '僕は、' + TARGET + 'が好き。' + TAIL


@pytest.mark.parametrize('tier,requested', (('free', 'short_essay'), ('plus', 'short_essay'), ('premium', 'quote'), ('premium', 'declaration')))
def test_bare_register_does_not_grant_format_or_excerpt_permissions(tier, requested):
    _, out = run('僕は' + TARGET + 'が好き。' + TAIL, tier=tier, requested_format=requested)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_b9_receives_the_exact_bare_body_and_all_reservations(ratio):
    class Metrics:
        profile_id = 'synthetic-bare-evaluation-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2, True)
    out = generated('僕は' + TARGET + 'が好き。' + TAIL)
    c = out.artifact.as_candidate()
    recipe = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = c['content_payload']['body_blocks']
    rebuilt = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
               for i in range(len(blocks))]
    assert rebuilt == blocks and '\n\n'.join(rebuilt) == c['piece_text']
    assert layout['piece_text_hash'] == c['piece_text_hash']
    assert not layout['clipped'] and not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0


def test_short_bare_input_is_not_padded_to_satisfy_a_format():
    _, out = run('僕は絵が好き。')
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.reason_codes == ('format_not_eligible',)


def test_bare_value_uses_the_existing_format_policy_without_inventing_a_vow():
    text = '私にとって' + TARGET + 'が大切。'
    out = generated(text, tier='premium', requested_format='declaration')
    assert out.artifact.format_type == 'declaration'
    assert out.artifact.piece_text == '私にとって、' + TARGET + 'が大切。'
    assert out.artifact_plan.declaration_eligible
    assert out.source_meaning.personal_evaluations[0].copula == ''
