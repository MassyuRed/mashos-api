"""Quoted speakers and operators stay inside their source-bound quotation.

Fictional CPU candidates and disposable SQL; no model call or training.
The existing outer scope grammar and independent S7 remain the owners.
"""
import json

import pytest

from cocolon_meaning_experience_engine.piece_source import _scoped_expression_match
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    prepare_piece_model_request, piece_model_source_plan)
from piece_model_source import build_piece_model_messages
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request
from test_piece_model_narrator_voice import evaluate
from test_b05_piece_model_saved_pipeline import _provider, _evidence
from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request


OUTER = '私は読書の時間を選びたい。'
WAIT = '友人が「私は待っているよ」と言ってくれたので、' + OUTER
INNER_REASON = '友人が「疲れたので、私は休みたい」と言ってくれたので、' + OUTER


def checked(saved, blocks):
    result = evaluate(saved, blocks)
    assert result.artifact, result.reason_codes
    req = request(saved)
    prepared = prepare_piece_model_request(req)
    before = saved, prepared.private_json, prepared.request_id
    material = json.loads(build_piece_model_messages(prepared,
        include_authoring_constraints=True, source_request=req)[1]['content'])
    assert before == (saved, prepared.private_json, prepared.request_id)
    return result, material


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('quoted', ['私は待っているよ', '疲れたので、私は休みたい',
                                   '都合が合うなら、私は休む'])
def test_only_outer_operator_and_narrator_own_the_reason_scope(speaker, quoted):
    text = '友人が「' + quoted + '」と言ってくれたので、' + OUTER.replace('私', speaker)
    result, material = checked(source(text, field='memo'), [text])
    meaning = result.source_meaning
    scope, = meaning.expression_scopes
    assert scope.relation == 'SOURCE_EXPLICIT_REASON' and scope.marker == 'ので'
    assert text[slice(*scope.scope_scalar_span)] == '友人が「' + quoted + '」と言ってくれたので'
    assert text[slice(*scope.expression_scalar_span)] == OUTER.replace('私', speaker)
    for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                         (scope.expression_scalar_span, scope.expression_utf8_span)):
        assert text[slice(*scalar)].encode() == meaning.envelope.raw_utf8[slice(*utf8)]
    slot = material['control']['authoring_constraints']['field_slots']['memo_0']
    quote, = slot['literal_quotes']
    assert text[quote['scalar_start']:quote['scalar_end']] == quote['literal'] == '「' + quoted + '」'
    assert result.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert not result.artifact_plan.declaration_eligible


@pytest.mark.parametrize('marker,relation', [
    ('なら', 'SOURCE_EXPLICIT_CONDITION'), ('けれど', 'SOURCE_EXPLICIT_CONCESSION')])
def test_outer_condition_or_concession_does_not_inherit_the_quoted_reason(marker, relation):
    text = INNER_REASON.replace('言ってくれたので、', '言ってくれた' + marker + '、')
    result, _ = checked(source(text, field='memo'), [text])
    scope, = result.source_meaning.expression_scopes
    assert scope.marker == marker and scope.relation == relation
    assert text[slice(*scope.expression_scalar_span)] == OUTER


@pytest.mark.parametrize('expression', [
    '私が選びたいのは、読書の時間です。', '私は読書が好きです。'])
def test_focal_and_evaluation_reuse_the_same_outer_quote_boundary(expression):
    text = WAIT[:-len(OUTER)] + expression
    result, material = checked(source(text, field='memo'), [text])
    scope, = result.source_meaning.expression_scopes
    assert text[slice(*scope.expression_scalar_span)] == expression
    quote, = material['control']['authoring_constraints']['field_slots']['memo_0']['literal_quotes']
    assert quote['literal'] == '「私は待っているよ」'


def test_quote_internal_reason_without_an_outer_operator_remains_opaque_context():
    report = '友人が「疲れたので、私は休みたい」と言ってくれた。'
    text = report + OUTER
    result, _ = checked(source(text, field='memo'), [text])
    assert result.source_meaning.expression_scopes == ()
    assert result.artifact_plan.duties[0].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
    assert _scoped_expression_match(report) is None


def test_quoted_material_cannot_supply_an_empty_outer_premise():
    assert _scoped_expression_match('ので、私は「休む」ということを選びたい。') is None


@pytest.mark.parametrize('replacement', [
    ('疲れたので、私は休みたい', '疲れたなら、私は休みたい'),
    ('疲れたので、私は休みたい', '疲れたので、僕は休みたい'),
    ('言ってくれたので、', '言ってくれたなら、'),
    ('言ってくれた', '言ってあげた'),
    ('、私は読書', '、読書'),
    ('、私は読書', '、僕は読書'),
    ('選びたい', '選んだ'),
    ('読書の時間', '料理の時間'),
])
def test_same_s7_rejects_quote_outer_scope_narrator_and_wish_changes(replacement):
    assert evaluate(source(INNER_REASON, field='memo'),
                    [INNER_REASON.replace(*replacement)]).artifact is None


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_scope_and_quote_coordinates_do_not_cross_saved_fields(field):
    other = '私は読書が好きです。'
    saved = source(INNER_REASON, field=field, other=other)
    blocks = [INNER_REASON, other] if field == 'memo' else [other, INNER_REASON]
    result, material = checked(saved, blocks)
    conditions = material['control']['authoring_constraints']['field_slots']
    quote_slots = [value for value in conditions.values() if 'literal_quotes' in value]
    assert len(quote_slots) == 1 and quote_slots[0]['field_path'] == field
    quote, = quote_slots[0]['literal_quotes']
    assert INNER_REASON[quote['scalar_start']:quote['scalar_end']] == quote['literal']
    scope, = result.source_meaning.expression_scopes
    original = result.source_meaning.envelope.raw_utf8.decode()
    assert original[slice(*scope.expression_scalar_span)] == OUTER


def test_refined_original_quote_scope_cannot_enter_the_separate_answer():
    saved = refined_source(original=INNER_REASON, answer='わたしは読書が好きです。')
    result, material = checked(saved, [INNER_REASON, 'わたしは読書が好きです。'])
    original, answer = material['sources']
    slots = material['control']['authoring_constraints']['field_slots']
    assert slots['memo_0']['source_id'] == original['source_id']
    assert slots['answer_text_private_1']['source_id'] == answer['source_id'] != original['source_id']
    assert 'literal_quotes' not in slots['answer_text_private_1']
    assert len(result.source_meaning.original.expression_scopes) == 1
    assert result.source_meaning.supplemental.expression_scopes == ()


@pytest.mark.parametrize('text', [
    WAIT.replace('ので、', 'ので'), WAIT.replace('ので、', 'から、'),
    WAIT.replace('「私は待っているよ」', '「私は待っているよ」「休むよ」'),
    WAIT.replace('「私は待っているよ」', '「私は『待っている』よ」'),
    WAIT.replace('「私は待っているよ」', '「私は\n待っているよ」'),
])
def test_unread_quote_or_unmarked_reason_does_not_gain_a_typed_outer_scope(text):
    # Do not turn older literal admission into a new typed relation.
    try:
        meaning, _ = piece_model_source_plan(request(source(text, field='memo')))
    except ValueError:
        return
    assert not meaning.expression_scopes


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case_id,text', [('quote-outer-self', WAIT), ('quote-outer-reason', INNER_REASON)])
def test_cpu_quote_scope_candidate_saves_once_and_replays_without_generation(
        saved_piece_db, monkeypatch, tier, case_id, text):
    seen = _provider(monkeypatch, case_id, [text])
    record = dict(id=case_id, created_at=saved_piece_db.query(
        'SELECT now()::text AS stamp')['rows'][0]['stamp'], memo=text, memo_action='',
        category=['生活'], emotions=['喜び'], emotion_details=[dict(type='喜び', strength='strong')])
    result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['piece_text'] == text
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1
    _evidence(case_id + '-' + tier, result, seen)
