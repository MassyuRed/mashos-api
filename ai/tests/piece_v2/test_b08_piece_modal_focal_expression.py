"""Source-written focal modality stays with its predicate, author and object.

Public synthetic sources; the existing plain modal owner, nominal resolver,
format selection and CMEE author remain authoritative. No inferred intent,
new predicate dictionary, changed envelope or enabled product route.
"""
from dataclasses import asdict, replace
import hashlib
import os
import subprocess
import sys

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, _FOCUS, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TIME = '朝に窓辺で葉の形をゆっくり眺める時間'
ACT = '浮かんだ言葉を小さな手帳に書き留めること'
TAIL = 'ただ、毎日続けるかはまだ決めていない。'
MODALS = ('かもしれない', 'とは限らない')
FORMS = (
    ('大切にしたい', False), ('大切にしている', False),
    ('大切にしたくない', False), ('望んでいる', False),
    ('望んでいない', False), ('選びたい', False), ('選びたくない', False),
    ('大切にしたかった', True), ('大切にしていた', True),
    ('大切にしたくなかった', True), ('望んでいた', True),
    ('望んでいなかった', True), ('選びたかった', True), ('選びたくなかった', True),
)


def outcome(text, *, tier='free', requested_format=None):
    source = PieceSourceSnapshot('synthetic-owner', 'modal-focal', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'modal-focal', source, source.owner_id, source.saved_input_id,
        source.source_version, tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode()
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for b in plan.block_node_ids for n in b) == tuple(
        n.node_id for n in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                            (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                            (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    frozen = asdict(meaning), asdict(plan)
    assert realize_piece_artifact(meaning, plan, tier=tier,
        requested_format=requested_format) == out.artifact
    assert frozen == (asdict(meaning), asdict(plan))
    source = PieceSourceSnapshot('synthetic-owner', 'modal-focal', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert not plan.declaration_eligible
    assert 'declaration' not in candidate['eligible_formats']
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('predicate,past', FORMS)
@pytest.mark.parametrize('modal', MODALS)
def test_whole_plain_modal_predicate_retains_its_negation_and_tense(predicate, past, modal):
    text = '私が' + predicate + modal + 'のは、' + TIME + 'です。'
    out = assert_body(text, '私は、' + TIME + 'を' + predicate + modal + '。')
    match = _FOCUS.fullmatch(text)
    assert match['predicate'] == predicate + modal
    assert match['modal'] == modal
    assert match['past_predicate'] == (predicate if past else None)
    assert out.artifact_plan.duties[0].operation == 'SOURCE_FOCAL_TO_FIRST_PERSON'
    assert out.artifact.eligible_formats == ('short_essay', 'quote')
    refused = outcome(text, tier='premium', requested_format='declaration')
    assert refused.status == EngineStatus.UNAVAILABLE
    assert refused.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_tentative_antecedent_does_not_set_the_next_evaluation(speaker):
    first = speaker + 'が望んでいなかったかもしれないのは、' + TIME + 'です。'
    second = 'その時間が好きとは限りません。'
    out = assert_body(first + speaker + 'は' + second + TAIL,
        speaker + 'は、' + TIME + 'を望んでいなかったかもしれない。' + second + TAIL)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert first[slice(*ref.antecedent_scalar_span)] == TIME
    frame, = out.source_meaning.personal_evaluations
    assert (frame.temporal_scope, frame.commitment) == ('NONPAST', 'NON_UNIVERSAL')


@pytest.mark.parametrize('premise,relation', (
    ('予定が空くなら', 'SOURCE_EXPLICIT_CONDITION'),
    ('予定が空くならば', 'SOURCE_EXPLICIT_CONDITION'),
    ('余裕がなかったので', 'SOURCE_EXPLICIT_REASON'),
    ('迷っていたけれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('迷っていたけれども', 'SOURCE_EXPLICIT_CONCESSION'),
    ('以前は', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
    ('当時も', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
    ('今は', 'SOURCE_EXPLICIT_TIME_CONTEXT'),
))
@pytest.mark.parametrize('modal', MODALS)
def test_outer_scope_does_not_assert_or_retime_the_inner_modal(premise, relation, modal):
    text = premise + '、私が大切にしたくなかった' + modal + 'のは、' + TIME + 'です。' + TAIL
    out = assert_body(text, premise + '、私は' + TIME + 'を大切にしたくなかった' + modal + '。' + TAIL)
    scope, = out.source_meaning.expression_scopes
    assert scope.relation == relation
    assert text[slice(*scope.scope_scalar_span)] == premise
    assert text[slice(*scope.expression_scalar_span)].startswith('私が大切にしたくなかった' + modal)


@pytest.mark.parametrize('word_order', ('focal', 'direct', 'evaluation'))
def test_two_prior_objects_keep_order_and_the_focal_modality(word_order):
    if word_order == 'focal':
        first = '私が望んでいるのは、' + TIME + 'です。'
        second = '私が選びたいのは、' + ACT + 'です。'
        rendered = '私は、' + TIME + 'を望んでいる。私は、' + ACT + 'を選びたい。'
    elif word_order == 'direct':
        first = '私は' + TIME + 'を望んでいます。'
        second = '私は' + ACT + 'を選びたい。'
        rendered = '私は、' + TIME + 'を望んでいます。私は、' + ACT + 'を選びたい。'
    else:
        first = '私にとって' + TIME + 'が大切です。'
        second = '私は' + ACT + 'が好きです。'
        rendered = '私にとって、' + TIME + 'が大切です。私は、' + ACT + 'が好きです。'
    focus = '当時は、私が大切にしていたかもしれないのは、このこととその時間です。'
    text = first + second + focus + TAIL
    out = assert_body(text, rendered + '当時は、私はこのこととその時間を大切にしていたかもしれない。' + TAIL)
    refs = out.source_meaning.nominal_references
    assert [r.antecedent_node_id for r in refs] == ['piece:s2', 'piece:s1']
    assert [text[slice(*r.reference_scalar_span)] for r in refs] == ['このこと', 'その時間']


def test_same_author_scope_omits_only_the_repeated_topic():
    text = '僕は迷っているけれど、僕が選びたくないかもしれないのは、' + TIME + 'です。' + TAIL
    assert_body(text, '僕は迷っているけれど、' + TIME + 'を選びたくないかもしれない。' + TAIL)


def test_public_role_and_unicode_keep_original_ranges_and_the_written_modal():
    target = '私の友人の三浦さんと🌿の形を静かに眺める時間'
    text = '\t以前は、僕が望んでいたとは限らないのは、' + target + 'です。\r\n　今は、僕はその時間が好きです。' + TAIL
    expected = '以前は、僕は私の友人と🌿の形を静かに眺める時間を望んでいたとは限らない。今は、僕はその時間が好きです。' + TAIL
    out = assert_body(text, expected)
    assert text[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_complete_single_statement_can_be_a_quote_but_not_a_pledge(tier):
    text = '私が望んでいるとは限らないのは、' + TIME + 'です。'
    out = assert_body(text, '私は、' + TIME + 'を望んでいるとは限らない。', tier=tier)
    assert out.artifact.format_type == ('short_essay' if tier == 'free' else 'quote')
    for fmt in ('short_essay', 'quote', 'declaration'):
        chosen = outcome(text, tier=tier, requested_format=fmt)
        permitted = tier == 'premium' and fmt != 'declaration'
        assert chosen.status == (EngineStatus.GENERATED if permitted else EngineStatus.UNAVAILABLE)
        if permitted:
            assert chosen.artifact.piece_text == out.artifact.piece_text


def test_context_and_later_reservation_cannot_be_excerpted():
    text = '学生のころは予定が少なかった。私が望んでいたかもしれないのは、' + TIME + 'です。' + TAIL
    assert_body(text, '学生のころは予定が少なかった。\n\n私は、' + TIME + 'を望んでいたかもしれない。\n\n' + TAIL)
    for fmt in ('quote', 'declaration'):
        refused = outcome(text, tier='premium', requested_format=fmt)
        assert refused.status == EngineStatus.UNAVAILABLE
        assert refused.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('text', (
    '彼が望んでいるかもしれないのは、' + TIME + 'です。',
    '望んでいるかもしれないのは、' + TIME + 'です。',
    '私が望んでいるかもしれないのは、その時間です。',
    '私が望んでいますかもしれないのは、' + TIME + 'です。',
    '私が望んでいましたかもしれないのは、' + TIME + 'です。',
    '私が選びたかったですとは限らないのは、' + TIME + 'です。',
    '私が望んでいるかもしれませんのは、' + TIME + 'です。',
    '私が望んでいるとは限りませんのは、' + TIME + 'です。',
    '私が望んでいるかもしれないとは限らないのは、' + TIME + 'です。',
    '私が選ぶかもしれないのは、' + TIME + 'です。',
    '私が望んでいるかもしれないのは、' + TIME + 'でした。',
    '私が望んでいるかもしれないのは、' + TIME + 'ですと聞いた。',
    '以前は私が望んでいるかもしれないのは、' + TIME + 'です。',
    '以前は、今は、私が望んでいるかもしれないのは、' + TIME + 'です。',
    '私は迷っているけれど、僕が望んでいるかもしれないのは、' + TIME + 'です。',
))
def test_modality_cannot_supply_author_referent_or_unadmitted_grammar(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_two_competing_prior_objects_stay_unresolved():
    text = ('私が望んでいるのは、' + TIME + 'です。'
            '私が選びたいのは、夜に机で写真を眺める時間です。'
            '私が大切にしたいかもしれないのは、その時間です。' + TAIL)
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('unresolved_reference',)


@pytest.mark.parametrize('change', ('declaration', 'predicate', 'duty', 'scope'))
def test_forged_meaning_or_plan_cannot_remove_modality_or_scope(change):
    text = '当時も、私が望んでいなかったかもしれないのは、' + TIME + 'です。' + TAIL
    out = assert_body(text, '当時も、私は' + TIME + 'を望んでいなかったかもしれない。' + TAIL)
    meaning, plan = out.source_meaning, out.artifact_plan
    if change == 'declaration':
        plan = replace(plan, declaration_eligible=True)
    elif change == 'predicate':
        nodes = meaning.graph.nodes
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(replace(
            nodes[0], value=nodes[0].value.replace('かもしれない', '')), *nodes[1:])))
    elif change == 'duty':
        plan = replace(plan, duties=(replace(plan.duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT'), *plan.duties[1:]))
    else:
        meaning = replace(meaning, expression_scopes=())
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_same_modal_text_reaches_the_existing_layout(ratio):
    text = '以前は、私が望んでいたかもしれないのは、' + TIME + 'です。' + TAIL
    out = assert_body(text, '以前は、私は' + TIME + 'を望んでいたかもしれない。' + TAIL)
    class Metrics:
        profile_id = 'synthetic-modal-focal-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']


@pytest.mark.parametrize('first', ('piece_v2_generation',
    'cocolon_meaning_experience_engine.piece_source',
    'cocolon_meaning_experience_engine.engine'))
def test_shared_modal_owner_works_in_each_cold_import_order(first):
    code = ('import importlib; importlib.import_module(' + repr(first) + '); '
            'from piece_v2_generation import _FOCUS; '
            'm=_FOCUS.fullmatch("私が望んでいたかもしれないのは、静かに過ごす時間です。"); '
            'assert m is not None and m["modal"] == "かもしれない"')
    env = dict(os.environ)
    result = subprocess.run([sys.executable, '-s', '-B', '-c', code], env=env,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_unresolved_deictic_in_later_context_is_not_silently_removed():
    text = '以前は、私が望んでいたかもしれないのは、' + TIME + 'です。' + 'ただ、これから毎日続けるかはまだ決めていない。'
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('unresolved_reference',)
