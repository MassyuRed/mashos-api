"""Independent SQL fences for real answer prefixes followed by corrections.

Only disposable PGlite and synthetic saved Emlis sources are used. Corruption
cases deliberately update both stored rows and the private expected snapshot;
matching that snapshot cannot replace independent source/receipt validation.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from uuid import uuid4

import pytest

from cocolon_meaning_experience_engine.emlis_thread_source import identity
from piece_v2_contract import canonical_sha256_hex
from test_b05_answer_correction_application import answer_correction_case
from test_b05_interpretation_correction_application import corrected_db, corrected_case
from test_b05_effective_round_sql_fence import effective_fence_db, _apply
from test_b05_natural_refined_saved_pipeline import (
    natural_refined_db, refined_pipeline_db, saved_piece_db,
)
from test_b05_refined_source_fence_sql import (
    SIGNATURES, _catalog, _issue_args, _mutation_args, _saved_args,
    _piece_state, _update, rpc,
)

MIGRATION = '20261115005742_piece_answer_and_interpretation_corrections.sql'
WRITERS = {'issue': 'piece_issue_preview_v2', 'visual': 'piece_mutate_preview_visual_v2',
           'save': 'piece_save_v2'}
CHANGES = (
    'selected_answer', 'selected_question', 'answer_is_parent', 'missing_answers',
    'reordered_answers', 'changed_answer_bytes', 'missing_checkpoints',
    'duplicate_checkpoint', 'unresolved_checkpoint', 'empty_checkpoint_update',
    'forged_inactive_claim', 'foreign_time_anchor', 'missing_prior_correction',
    'reordered_corrections', 'missing_prior_checkpoint', 'missing_prior_receipt',
    'prior_receipt_stage', 'receipt_reply', 'answer_finish_clock',
    'stop_after_person_write', 'middle_finish_after_person_write',
    'answer_after_correction', 'earlier_correction_target', 'needs_detail',
    'latest_only_correction_prefix', 'coherent_forged_prefix', 'expected_event_graft',
)


@pytest.fixture(scope='module')
def mixed_fence_db(corrected_db):
    before = _catalog(corrected_db)
    _apply(corrected_db, MIGRATION)
    corrected_db.mixed_fence_catalog = (before, _catalog(corrected_db))
    return corrected_db


def _sql_case(case):
    case = dict(case)
    row = case['record']
    keys = ('source_lineage', 'format_type', 'content_payload', 'content_payload_hash',
            'piece_text', 'piece_text_hash', 'safety_state', 'visual_recipe',
            'visual_recipe_hash', 'renderer_version')
    case['record'] = {key: deepcopy(row[key]) for key in keys}
    case['record']['eligible_formats'] = deepcopy(row['preview_eligible_formats'])
    return case


def _args(db, case, operation):
    return (_issue_args(case) if operation == 'issue' else
            _mutation_args(db, case, case['issued']) if operation == 'visual' else
            _saved_args(case, case['issued']))


def _write_event(db, event):
    _update(db, 'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',
            [event['id'], json.dumps(event['payload'], ensure_ascii=False)])


def _sync(db, case, args):
    frozen = args['p_expected_source_state']['interpretation_correction']
    tid = case['snapshot']['thread']['id']
    frozen['events'] = [r['row'] for r in db.query(
        'SELECT to_jsonb(e) AS row FROM public.emlis_thread_events e '
        'WHERE thread_id=$1 ORDER BY seq', [tid])['rows']]
    frozen['thread_data'] = db.query(
        'SELECT data FROM public.emlis_input_threads WHERE id=$1', [tid])['rows'][0]['data']


def _substitute(value, old, new):
    if isinstance(value, dict):
        return {k: _substitute(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute(v, old, new) for v in value]
    return new if value == old else value


def _lineage(db, case, args, lineage):
    args['p_expected_source_state']['lineage'] = deepcopy(lineage)
    if 'p_record' in args:
        args['p_record']['source_lineage'] = deepcopy(lineage)
    else:
        _update(db, 'UPDATE public.piece_records SET source_lineage=$2::jsonb WHERE id=$1',
                [case['issued']['preview_id'], json.dumps(lineage, ensure_ascii=False)])
        if 'p_expected_record' in args:
            args['p_expected_record']['source_lineage'] = deepcopy(lineage)


def _corrupt(db, case, args, change):
    expected = args['p_expected_source_state']
    frozen = expected['interpretation_correction']
    events = deepcopy(frozen['events'])
    answers = [e for e in events if e['kind'] == 'ANSWER']
    questions = [e for e in events if e['kind'] == 'QUESTION']
    checkpoints = [e for e in events if e['kind'] == 'MEANING_UPDATE']
    refined = [e for e in events if e['kind'] == 'OBSERVATION' and e['payload']['stage'] == 'REFINED']
    corrected = [e for e in events if e['kind'] == 'OBSERVATION' and e['payload']['stage'] == 'CORRECTED']
    terminal, = [e for e in events if e['kind'] == 'TERMINAL']
    correction_events = [e for e in events if e['kind'] == 'OPERATION'
                         and e['payload'].get('stage') == 'INTERPRETATION_CORRECTION']

    def paired(body, stage=None, status=None):
        return next(e for e in events if e['kind'] == 'OPERATION'
                    and e['operation_id'] == body['operation_id']
                    and e['attempt_id'] == body['attempt_id']
                    and (stage is None or e['payload'].get('stage') == stage)
                    and (status is None or e['payload'].get('status') == status))

    if change in {'selected_answer', 'selected_question', 'answer_is_parent'}:
        line = deepcopy(expected['lineage'])
        key = 'question_need_decision_identity' if change == 'selected_question' else 'supplemental_answer_identity'
        line['observation'][key] = (questions[0]['id'] if change == 'selected_question' else
                                    case['parent'] if change == 'answer_is_parent' else answers[0]['id'])
        if change == 'answer_is_parent':
            # An existing preview remains genuine while the writer receives
            # a parent identity falsely asserted as the selected answer.
            expected['lineage'] = line
            if 'p_record' in args:
                args['p_record']['source_lineage'] = deepcopy(line)
            elif 'p_expected_record' in args:
                args['p_expected_record']['source_lineage'] = deepcopy(line)
        else:
            _lineage(db, case, args, line)
    elif change == 'missing_answers':
        del frozen['answer_sources']
    elif change == 'reordered_answers':
        frozen['answer_sources'].reverse()
    elif change == 'changed_answer_bytes':
        event = answers[-1]
        event['payload']['source']['answer_text_private'] += '変更'
        frozen['answer_sources'][-1] = deepcopy(event['payload']['source'])
        _write_event(db, event)
    elif change == 'missing_checkpoints':
        del frozen['answer_checkpoints']
    elif change == 'duplicate_checkpoint':
        frozen['answer_checkpoints'][-1] = deepcopy(frozen['answer_checkpoints'][0])
    elif change in {'unresolved_checkpoint', 'empty_checkpoint_update', 'forged_inactive_claim', 'foreign_time_anchor'}:
        event = checkpoints[0]
        if change == 'unresolved_checkpoint':
            event['payload']['assessment_status'] = 'UNRESOLVED'
        elif change == 'empty_checkpoint_update':
            event['payload']['answer_update']['updates'] = []
        elif change == 'forged_inactive_claim':
            event['payload']['inactive_claim_refs'] = ['nucleus:s999']
        else:
            event['payload']['answer_update']['updates'][0]['temporal_binding']['anchor_source_ref'] = 'src-' + 'f' * 24
        frozen['answer_checkpoints'][0] = deepcopy(event['payload'])
        _write_event(db, event)
    elif change == 'missing_prior_correction':
        del frozen['prior_sources']
    elif change == 'reordered_corrections':
        frozen['source'], frozen['prior_sources'][0] = frozen['prior_sources'][0], frozen['source']
    elif change in {'missing_prior_checkpoint', 'missing_prior_receipt'}:
        event = checkpoints[0] if change == 'missing_prior_checkpoint' else paired(refined[0], stage='NATURAL_REPLY_RECEIVED')
        _update(db, 'DELETE FROM public.emlis_thread_events WHERE id=$1', [event['id']])
    elif change in {'prior_receipt_stage', 'receipt_reply'}:
        event = paired(refined[0], stage='NATURAL_REPLY_RECEIVED')
        if change == 'prior_receipt_stage':
            event['payload']['response_stage'] = 'FINAL'
        else:
            event['payload']['reply']['text'] += '変更'
        _write_event(db, event)
    elif change == 'answer_finish_clock':
        event = paired(refined[-1], status='AWAITING_CONTINUE')
        stamp = (datetime.fromisoformat(refined[-1]['recorded_at']) - timedelta(microseconds=1)).isoformat()
        _update(db, 'UPDATE public.emlis_thread_events SET recorded_at=$2 WHERE id=$1', [event['id'], stamp])
    elif change == 'stop_after_person_write':
        written = correction_events[0]['payload']['source']['recorded_at']
        stamp = (datetime.fromisoformat(written) + timedelta(microseconds=1)).isoformat()
        _update(db, 'UPDATE public.emlis_thread_events SET recorded_at=$2 WHERE id=$1', [terminal['id'], stamp])
    elif change == 'middle_finish_after_person_write':
        event = paired(corrected[0], status='COMPLETED')
        stamp = (datetime.fromisoformat(frozen['source']['recorded_at']) + timedelta(microseconds=1)).isoformat()
        _update(db, 'UPDATE public.emlis_thread_events SET recorded_at=$2 WHERE id=$1', [event['id'], stamp])
    elif change == 'answer_after_correction':
        seq = max(e['seq'] for e in events) + 1
        _update(db, 'UPDATE public.emlis_thread_events SET seq=$2 WHERE id=$1', [answers[-1]['id'], seq])
    elif change == 'earlier_correction_target':
        event = correction_events[-1]
        event['payload']['source']['target_event_id'] = refined[-1]['id']
        frozen['source'] = deepcopy(event['payload']['source'])
        _write_event(db, event)
        line = deepcopy(expected['lineage'])
        line['interpretation_correction_source']['target_event_id'] = refined[-1]['id']
        line['interpretation_correction_source']['source_version'] = 'sha256:' + canonical_sha256_hex(frozen['source'])
        _lineage(db, case, args, line)
    elif change == 'needs_detail':
        event = correction_events[0]
        event['payload']['assessment'] = 'NEEDS_DETAIL'
        _write_event(db, event)
    elif change in {'latest_only_correction_prefix', 'coherent_forged_prefix'}:
        old = frozen['source_prefix_ref']
        forged = (identity('emlis-corrected-source-prefix', refined[-1]['payload']['source_prefix_ref'],
                           (frozen['source'],)) if change == 'latest_only_correction_prefix' else
                  'emlis-corrected-source-prefix-' + 'f' * 64)
        assert forged != old
        for event in events:
            changed = _substitute(event, old, forged)
            if changed != event:
                _write_event(db, changed)
        data = _substitute(frozen['thread_data'], old, forged)
        _update(db, 'UPDATE public.emlis_input_threads SET source_prefix_ref=$2,data=$3::jsonb WHERE id=$1',
                [case['snapshot']['thread']['id'], forged, json.dumps(data, ensure_ascii=False)])
        frozen['source_prefix_ref'] = forged
    elif change != 'expected_event_graft':
        raise AssertionError(change)
    _sync(db, case, args)
    if change == 'expected_event_graft':
        frozen['events'][0]['payload']['unrecorded'] = True


def test_mixed_source_migration_preserves_function_catalog_and_existing_primitive(mixed_fence_db):
    db = mixed_fence_db
    assert db.mixed_fence_catalog[0] == db.mixed_fence_catalog[1]
    for signature in SIGNATURES:
        for role, expected in [('anon', False), ('authenticated', False), ('service_role', True)]:
            result = db.query("SELECT has_function_privilege($1,$2,'EXECUTE') AS allowed", [role, signature])
            assert result['rows'][0]['allowed'] is expected


@pytest.mark.parametrize('operation', tuple(WRITERS))
def test_all_writers_reject_coherently_corrupted_answer_and_correction_history(
        mixed_fence_db, monkeypatch, operation):
    db = mixed_fence_db
    case = _sql_case(answer_correction_case(db, monkeypatch, tier='premium', rounds=2,
        extra_explanations=('「私は仕事を続けたい」は取り消します。',)))
    frozen = case['expected']['interpretation_correction']
    assert len(frozen['answer_sources']) == len(frozen['answer_checkpoints']) == 2
    assert len(frozen['prior_sources']) == 1
    assert any(e['kind'] == 'TERMINAL' for e in frozen['events'])
    # Establish the unmodified route before deliberately corrupting its state.
    assert 'code' not in db.query('BEGIN')
    try:
        control = rpc(db, WRITERS[operation], _args(db, case, operation))
        assert 'code' not in control, (operation, control)
    finally:
        assert 'code' not in db.query('ROLLBACK')
    failures = []
    for change in CHANGES:
        assert 'code' not in db.query('BEGIN')
        try:
            args = _args(db, case, operation)
            _corrupt(db, case, args, change)
            before = _piece_state(db)
            result = rpc(db, WRITERS[operation], args)
            assert result == {'code': 'P0001', 'message': 'PIECE_CONFLICT'}, (operation, change, result)
            assert _piece_state(db) == before
        except AssertionError as exc:
            failures.append((change, str(exc)))
        finally:
            assert 'code' not in db.query('ROLLBACK')
    assert not failures, (operation, failures)


@pytest.mark.parametrize('operation', tuple(WRITERS))
def test_no_answer_thread_cannot_borrow_mixed_lineage(mixed_fence_db, monkeypatch, operation):
    db = mixed_fence_db
    case = _sql_case(corrected_case(None, db, monkeypatch, tier='premium'))
    assert case['snapshot']['thread']['latest_answer_event_id'] is None
    assert 'code' not in db.query('BEGIN')
    try:
        args = _args(db, case, operation)
        line = deepcopy(args['p_expected_source_state']['lineage'])
        line['semantic_source_roles'] = ['original_input', 'supplemental_answer', 'interpretation_correction']
        line['lineage_control_roles'] = ['emlis_observation_result', 'question_need_decision', 'ai_interpretation_target']
        line['observation'].update(question_need_decision_identity=str(uuid4()),
            supplemental_answer_identity=str(uuid4()), supplemental_answer_version='cocolon.cmee.supplemental_answer.v1',
            supplemental_answer_bundle_commitment='sha256:' + 'a' * 64)
        _lineage(db, case, args, line)
        before = _piece_state(db)
        result = rpc(db, WRITERS[operation], args)
        assert result == {'code': 'P0001', 'message': 'PIECE_CONFLICT'}, result
        assert _piece_state(db) == before
    finally:
        assert 'code' not in db.query('ROLLBACK')
