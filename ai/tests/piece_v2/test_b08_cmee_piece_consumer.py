"""Synthetic CMEE Piece source/plan/author integration; no user review material."""
import dataclasses
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine import engine
from cocolon_meaning_experience_engine.contracts import (
    EngineStatus, GenerationRequest, GroundedMeaningGraph,
)
from cocolon_meaning_experience_engine.piece_source import build_piece_source_meaning
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, PieceEngineOutcome, compile_piece_artifact_plan,
    realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


TEXT = '友人の佐藤さんと話した。私は自分で納得してから答えを決めたい。'


def request(text=TEXT, **changes):
    result = PieceGenerationRequest('synthetic-request',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-saved', 'v1', text),
        'synthetic-owner', 'synthetic-saved', 'v1')
    return dataclasses.replace(result, **changes)


def run(text=TEXT, **changes):
    return engine.MeaningExperienceEngine().generate(request(text, **changes))


def must_generate(text=TEXT, **changes):
    out = run(text, **changes)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact is not None and out.artifact_plan is not None
    return out


def test_existing_b8_entry_really_calls_cmee_piece_and_returns_its_artifact(monkeypatch):
    seen = []
    original = engine.MeaningExperienceEngine.generate
    def observe(self, req):
        out = original(self, req)
        seen.append((req, out))
        return out
    monkeypatch.setattr(engine.MeaningExperienceEngine, 'generate', observe)
    out = generate_piece_candidate(request().source, authenticated_owner_id='synthetic-owner')
    assert len(seen) == 1 and type(seen[0][0]) is PieceGenerationRequest
    assert out == seen[0][1].artifact.as_candidate()
    assert out['piece_text'] == '私は、自分で納得してから答えを決めたい。\n\n友人と話した。'
    assert not out['production_enabled'] and out['record_effect'] == out['quota_effect'] == 0


def test_no_emlis_artifact_or_previous_paragraph_author_is_used(monkeypatch):
    import piece_v2_expression
    def forbidden(*args, **kwargs):
        raise AssertionError('wrong consumer')
    monkeypatch.setattr(engine, 'build_text_grounded_limited_artifact', forbidden)
    monkeypatch.setattr(engine, 'freeze_text_source', forbidden)
    monkeypatch.setattr(piece_v2_expression, 'compile_piece_expression_plan', forbidden)
    out = must_generate()
    assert type(out.source_meaning.graph) is GroundedMeaningGraph
    assert out.artifact_plan.intent.product_job == 'EXPRESS_AND_SHARE'
    assert out.artifact_plan.graph_id == out.source_meaning.graph.graph_id


@pytest.mark.parametrize('text', [
    '私は自分で納得できるまで、焦らずに自分の答えを考えたい。',
    '私は自分で納得してから答えを決めたい。昨日は時間が足りなかった。まだ迷っている。',
    '昨日は時間が足りなかった。私は自分で納得してから答えを決めたい。まだ迷っている。',
])
def test_single_or_nonfinal_intent_is_admitted_without_cutting_its_qualification(text):
    out = must_generate(text)
    expected = text.replace('私は', '私は、')
    if text.startswith('昨日'):
        expected = expected.replace('昨日は時間が足りなかった。', '昨日は時間が足りなかった。\n\n')
    assert out.artifact.piece_text == expected
    if text.count('。') > 1:
        assert out.artifact.eligible_formats == ('short_essay',)
        assert out.artifact.body_blocks[-1].endswith('まだ迷っている。')
        assert '答えを決めたい。' in out.artifact.body_blocks[-1]


def test_user_stated_role_abstraction_keeps_past_negation_condition_and_current_uncertainty():
    text = ('昨日は上司の田中さんに相談しなかった。'
            '私は気持ちが整理できたら、自分の考えを伝えたい。'
            'まだ、いつ話すかは決めていない。')
    out = must_generate(text)
    assert out.artifact.piece_text == (
        '昨日は上司に相談しなかった。\n\n'
        '私は、気持ちが整理できたら、自分の考えを伝えたい。'
        'まだ、いつ話すかは決めていない。')
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert out.artifact.eligible_formats == ('short_essay',)


def test_repeated_named_reference_uses_only_its_explicit_source_role():
    text = ('同僚の山田さんと話した。山田さんには、まだ結論を伝えていない。'
            '私は答えを急がず、自分の考えを整理したい。')
    out = must_generate(text)
    assert out.artifact.piece_text == ('私は、答えを急がず、自分の考えを整理したい。\n\n'
                                       '同僚と話した。同僚には、まだ結論を伝えていない。')
    assert '山田' not in out.artifact.piece_text


@pytest.mark.parametrize('context,reason', [
    ('佐藤さんと話した。', 'public_role_binding_missing'),
    ('友人の佐藤さんと友人の田中さんは考え方が違った。', 'public_role_binding_ambiguous'),
    ('友人の佐藤さんと上司の佐藤さんに会った。', 'public_role_binding_ambiguous'),
    ('友人の佐藤さんという名前を覚えた。', 'public_identity_is_material'),
    ('友人の佐藤さんと呼ぶことにした。', 'public_identity_is_material'),
])
def test_no_unbound_identity_or_loss_of_person_distinction(context, reason):
    out = run(context + '私は答えを急がず、自分の考えを整理したい。')
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.reason_codes == (reason,)


@pytest.mark.parametrize('changes', [
    {'expected_owner_id': 'other'}, {'expected_saved_input_id': 'another'},
    {'expected_source_version': 'v2'}, {'expected_owner_id': ' '},
])
def test_source_identity_binding_is_checked_by_cmee_not_only_the_b8_wrapper(changes):
    out = run(**changes)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('changes', [
    {'core_id': 'emlis_ai'}, {'product_job': 'OBSERVE_AND_CLARIFY'},
    {'execution_mode': 'EMLIS_APPLICATION'}, {'execution_mode': 'PRODUCTION'},
    {'request_id': ''}, {'request_id': None},
])
def test_piece_request_cannot_enable_or_impersonate_another_core(changes):
    out = run(**changes)
    assert type(out) is PieceEngineOutcome
    assert out.status == EngineStatus.REJECTED and out.artifact is None
    assert out.as_body_free()['core_id'] == 'piece'
    assert not out.automatic_progression


def test_emlis_dispatch_remains_on_its_original_body_path(monkeypatch):
    called = []
    sentinel = object()
    def original_body(self, req):
        called.append(req)
        return sentinel
    monkeypatch.setattr(engine.MeaningExperienceEngine, '_generate_original_body', original_body)
    req = GenerationRequest('synthetic-emlis', None, 'saved')
    assert engine.MeaningExperienceEngine().generate(req) is sentinel
    assert called == [req]
    old_shape_piece = dataclasses.replace(req, core_id='piece')
    rejected = engine.MeaningExperienceEngine().generate(old_shape_piece)
    assert rejected.reason_codes == ('core_id_out_of_scope',)


def test_every_original_sentence_and_exact_utf8_range_survives_shared_dedup():
    text = ('友人の佐藤さんと話した。友人の佐藤さんと話した。'
            '私は一人で考える時間も、急がずに大切にしたい。')
    out = must_generate(text)
    meaning = out.source_meaning
    assert len(meaning.graph.nodes) == len(meaning.sentences) == len(meaning.evidence) == 3
    assert out.artifact.piece_text.count('友人と話した。') == 2
    assert len(meaning.graph.required_owner_refs) == 3
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence):
        assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == node.value
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert hashlib.sha256(node.value.encode()).hexdigest() == evidence.literal_sha256
    assert {edge.relation for edge in meaning.graph.edges} == {'SOURCE_ORDER'}


def test_changed_source_version_has_a_distinct_bound_graph():
    a = must_generate()
    req = request(source=dataclasses.replace(request().source, source_version='v2'),
                  expected_source_version='v2')
    b = engine.MeaningExperienceEngine().generate(req)
    assert b.status == EngineStatus.GENERATED
    assert a.source_meaning.graph.graph_id != b.source_meaning.graph.graph_id
    assert a.artifact.piece_text == b.artifact.piece_text


@pytest.mark.parametrize('mutation', ['graph', 'coverage', 'declaration', 'order'])
def test_plan_cannot_drop_or_detach_meaning_or_promote_uncertainty(mutation):
    out = must_generate('昨日は時間が足りなかった。私は自分で納得してから答えを決めたい。まだ迷っている。')
    plan = out.artifact_plan
    if mutation == 'graph': plan = dataclasses.replace(plan, graph_id='different')
    if mutation == 'coverage': plan = dataclasses.replace(plan, block_node_ids=plan.block_node_ids[:1])
    if mutation == 'declaration': plan = dataclasses.replace(plan, declaration_eligible=True)
    if mutation == 'order': plan = dataclasses.replace(plan, block_node_ids=tuple(reversed(plan.block_node_ids)))
    with pytest.raises(ValueError):
        realize_piece_artifact(out.source_meaning, plan, tier='premium', requested_format=None)


def test_role_replacement_must_itself_exist_in_the_original_source():
    out = must_generate()
    binding = dataclasses.replace(out.source_meaning.role_bindings[0], role='上司')
    forged = dataclasses.replace(out.source_meaning, role_bindings=(binding,))
    with pytest.raises(ValueError):
        realize_piece_artifact(forged, out.artifact_plan, tier='free', requested_format=None)


def test_private_fields_and_original_name_do_not_escape_body_free_outcome_or_repr():
    out = must_generate()
    encoded = json.dumps(out.as_body_free(), ensure_ascii=False) + repr(out) + repr(request())
    for private in ('佐藤', TEXT, 'synthetic-owner', 'synthetic-saved', out.source_meaning.envelope.raw_sha256):
        assert private not in encoded
    assert 'observation' not in out.as_body_free() and 'reception' not in out.as_body_free()
    candidate = out.artifact.as_candidate()
    candidate['content_payload']['body_blocks'][0] = 'changed'
    assert out.artifact.as_candidate()['piece_text'] != 'changed'
    assert out.artifact.as_candidate()['content_payload']['body_blocks'][0] != 'changed'


def test_unexpected_private_exception_has_no_body_or_fallback(monkeypatch):
    from cocolon_meaning_experience_engine import piece_v1c
    def crash(*args, **kwargs):
        raise RuntimeError(TEXT)
    monkeypatch.setattr(piece_v1c, 'build_piece_source_meaning', crash)
    out = run()
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.reason_codes == ('piece_vertical_internal_failure',)
    assert TEXT not in json.dumps(out.as_body_free(), ensure_ascii=False)


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_same_cmee_canonical_body_reaches_existing_b9_layout(ratio):
    class Metrics:
        profile_id = 'synthetic-contract-metrics-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8,
                                   len(text)*font_px, font_px*.2, True)
    out = must_generate()
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'],
                                       candidate['piece_text_hash']) == out.artifact.piece_text
    recovered = [''.join(row['text'] for row in layout['lines'] if row['block_index'] == index)
                 for index in range(len(out.artifact.body_blocks))]
    assert recovered == list(out.artifact.body_blocks)
    assert '佐藤' not in ''.join(recovered)
