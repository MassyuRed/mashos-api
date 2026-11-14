"""Saved person-correction fences over disposable SQL, with synthetic authors.

Accepted sources come from the real two-input Emlis application helper. The
coherent edits below deliberately corrupt saved controls and never claim new
semantic admission, real-model quality, hosted writes or native rendering.
"""
from copy import deepcopy
import json

import pytest

from cocolon_meaning_experience_engine.emlis_thread_source import identity
from piece_v2_contract import canonical_sha256_hex
from test_b05_effective_round_sql_fence import effective_fence_db, _apply
from test_b05_effective_round_sql_fence import _case as _answer_case
from test_b05_piece_answer_update_saved_pipeline import prepare_answer_update
from test_b05_natural_refined_saved_pipeline import (
    natural_refined_db, refined_pipeline_db, saved_piece_db,
)
from test_b05_refined_source_fence_sql import (
    SIGNATURES, _catalog, _issue_args, _mutation_args, _saved_args,
    _piece_state, _update, rpc,
)

MIGRATION = '20261114213309_piece_interpretation_correction_source.sql'


@pytest.fixture(scope='module')
def corrected_sql_db(effective_fence_db):
    db = effective_fence_db
    before = _catalog(db)
    _apply(db, MIGRATION)
    db.corrected_catalog = (before, _catalog(db))
    return db


def test_corrected_migration_preserves_signatures_acl_rls_and_primitive(corrected_sql_db):
    db = corrected_sql_db
    assert db.corrected_catalog[0] == db.corrected_catalog[1]
    for signature in SIGNATURES:
        for role, expected in [('anon', False), ('authenticated', False), ('service_role', True)]:
            result = db.query("SELECT has_function_privilege($1,$2,'EXECUTE') AS allowed",
                [role, signature])
            assert result['rows'][0]['allowed'] is expected


def _case(db, monkeypatch, *, operation='REVISE'):
    from test_b05_interpretation_correction_application import corrected_case
    case = corrected_case(None, db, monkeypatch, operation=operation, tier='premium')
    row = case['record']
    keys = ('source_lineage','format_type','content_payload','content_payload_hash',
        'piece_text','piece_text_hash','safety_state','visual_recipe','visual_recipe_hash','renderer_version')
    case['record'] = {key: deepcopy(row[key]) for key in keys}
    case['record']['eligible_formats'] = deepcopy(row['preview_eligible_formats'])
    return case


def test_corrected_prefix_matches_person_source_and_independent_sql(corrected_sql_db, monkeypatch):
    db = corrected_sql_db
    case = _case(db, monkeypatch)
    frozen = case['expected']['interpretation_correction']
    source = frozen['source']
    target = next(event for event in frozen['events'] if event['id']==source['target_event_id'])
    original_prefix = target['payload']['source_prefix_ref']
    expected = identity('emlis-corrected-source-prefix', original_prefix, (source,))
    # SQL independently serializes the complete metadata key set in lexical
    # order. The target reply's prose is never used as person-meaning input.
    observed = db.query("""WITH metadata AS (
        SELECT '{'||string_agg(to_jsonb(key)::text||':'||value::text,',' ORDER BY key)||'}' AS body
        FROM jsonb_each($2::jsonb))
        SELECT 'emlis-corrected-source-prefix-'||encode(sha256(convert_to(
            '['||to_jsonb($1::text)::text||',['||body||']]','UTF8')),'hex') AS prefix
        FROM metadata""", [original_prefix, json.dumps(source, ensure_ascii=False)])
    assert observed['rows'][0]['prefix'] == expected == frozen['source_prefix_ref']
    assert case['snapshot']['thread']['source_prefix_ref'] == expected


@pytest.mark.parametrize('operation', ['issue','visual','save'])
def test_all_writers_reject_coherently_forged_corrected_prefix(corrected_sql_db, monkeypatch, operation):
    db = corrected_sql_db
    case = _case(db, monkeypatch)
    args = (_issue_args(case) if operation=='issue' else
        _mutation_args(db, case, case['issued']) if operation=='visual' else _saved_args(case, case['issued']))
    frozen = args['p_expected_source_state']['interpretation_correction']
    original_prefix = frozen['source_prefix_ref']
    forged_prefix = 'emlis-corrected-source-prefix-' + 'f'*64
    assert forged_prefix != original_prefix

    def substitute(value):
        if isinstance(value, dict):
            return {key: substitute(item) for key, item in value.items()}
        if isinstance(value, list):
            return [substitute(item) for item in value]
        return forged_prefix if value == original_prefix else value

    assert 'code' not in db.query('BEGIN')
    try:
        for event in frozen['events']:
            altered = substitute(event)
            if altered != event:
                _write_event(db, altered)
        data = substitute(frozen['thread_data'])
        _update(db, 'UPDATE public.emlis_input_threads SET source_prefix_ref=$2,data=$3::jsonb WHERE id=$1',
            [case['snapshot']['thread']['id'], forged_prefix, json.dumps(data, ensure_ascii=False)])
        frozen['source_prefix_ref'] = forged_prefix
        _sync_expected(db, case, args)
        body = next(event for event in frozen['events'] if event['kind']=='OBSERVATION'
            and event['payload']['stage']=='CORRECTED')
        receipt = next(event for event in frozen['events'] if event['kind']=='OPERATION'
            and event['payload'].get('stage')=='NATURAL_REPLY_RECEIVED'
            and event['operation_id']==body['operation_id'])
        assert body['payload']['source_prefix_ref'] == receipt['payload']['source_prefix_ref'] == forged_prefix
        assert receipt['payload']['reply']['source_prefix_ref'] == forged_prefix
        assert frozen['source'] == case['expected']['interpretation_correction']['source']
        before = _piece_state(db)
        result = rpc(db, {'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2',
            'save':'piece_save_v2'}[operation], args)
        assert result == {'code':'P0001','message':'PIECE_CONFLICT'}, result
        assert _piece_state(db) == before
    finally:
        assert 'code' not in db.query('ROLLBACK')


@pytest.mark.parametrize('change', ['REVISE', 'WITHDRAW'])
def test_corrected_source_reaches_issue_visual_save_and_one_quota(corrected_sql_db, monkeypatch, change):
    db = corrected_sql_db
    case = _case(db, monkeypatch, operation=change)
    assert set(case['expected']) == {'original','thread_id','thread_revision','lineage','interpretation_correction'}
    assert case['expected']['lineage']['observation']['emlis_observation_stage'] == 'corrected_observation'
    issued = rpc(db, 'piece_issue_preview_v2', _issue_args(case))
    assert 'code' not in issued, issued
    visual = rpc(db, 'piece_mutate_preview_visual_v2', _mutation_args(db, case, issued))
    assert 'code' not in visual, visual
    saved = rpc(db, 'piece_save_v2', _saved_args(case, visual))
    assert 'code' not in saved, saved
    count = db.query('SELECT count(*)::int AS count FROM public.piece_quota_consumptions WHERE owner_user_id=$1',
        [case['owner']])
    assert count['rows'][0]['count'] == 1


def _write_event(db, event):
    _update(db, 'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',
        [event['id'], json.dumps(event['payload'], ensure_ascii=False)])


def _sync_expected(db, case, args):
    thread_id = case['snapshot']['thread']['id']
    expected = args['p_expected_source_state']['interpretation_correction']
    expected['events'] = db.query('SELECT to_jsonb(e) AS row FROM public.emlis_thread_events e WHERE thread_id=$1 ORDER BY seq',
        [thread_id])['rows']
    expected['events'] = [row['row'] for row in expected['events']]
    expected['thread_data'] = db.query('SELECT data FROM public.emlis_input_threads WHERE id=$1',
        [thread_id])['rows'][0]['data']


def _coherent_change(db, case, args, change):
    expectation = args['p_expected_source_state']
    frozen = expectation['interpretation_correction']
    events = deepcopy(frozen['events'])
    correction = next(e for e in events if e['kind']=='OPERATION'
        and e['payload'].get('stage')=='INTERPRETATION_CORRECTION')
    target = next(e for e in events if e['id']==correction['payload']['source']['target_event_id'])
    current = next(e for e in events if e['kind']=='OBSERVATION' and e['payload']['stage']=='CORRECTED')
    if change in ('metadata_digest','explanation_digest'):
        key = 'source_version' if change=='metadata_digest' else 'explanation_commitment'
        expectation['lineage']['interpretation_correction_source'][key] = 'sha256:' + '0'*64
    elif change == 'target_is_current':
        correction['payload']['source']['target_event_id'] = current['id']
        frozen['source'] = deepcopy(correction['payload']['source'])
        info = expectation['lineage']['interpretation_correction_source']
        info['target_event_id'] = current['id']
        info['source_version'] = 'sha256:' + canonical_sha256_hex(frozen['source'])
        _write_event(db, correction)
    elif change == 'duplicate_excerpt':
        target['payload']['text'] += target['payload']['text']
        target['payload']['artifact']['text'] = target['payload']['text']
        received = next(e for e in events if e['kind']=='OPERATION'
            and e['operation_id']==target['operation_id']
            and e['payload'].get('stage')=='NATURAL_REPLY_RECEIVED')
        received['payload']['reply']['text'] = target['payload']['text']
        _write_event(db, target)
        _write_event(db, received)
    elif change == 'receipt_stage':
        for event in events:
            if (event['operation_id']==current['operation_id'] and event['kind']=='OPERATION'
                    and event['payload'].get('stage') in ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED')):
                event['payload']['response_stage'] = 'CORRECTED'
                _write_event(db, event)
    elif change == 'context_digest':
        current['payload']['context_ref'] = 'context-' + '0'*64
        _write_event(db, current)
        for event in events:
            if (event['operation_id']==current['operation_id'] and event['kind']=='OPERATION'
                    and event['payload'].get('stage') in ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED')):
                event['payload']['context_ref'] = current['payload']['context_ref']
                _write_event(db, event)
    elif change == 'needs_detail':
        correction['payload']['assessment'] = 'NEEDS_DETAIL'
        _write_event(db, correction)
    elif change == 'finish_before_observation':
        finish = next(e for e in events if e['kind']=='OPERATION'
            and e['operation_id']==current['operation_id'] and e['payload'].get('status')=='COMPLETED')
        _update(db, 'UPDATE public.emlis_thread_events SET recorded_at=$2 WHERE id=$1',
            [finish['id'], target['recorded_at']])
    else:
        raise AssertionError(change)
    _sync_expected(db, case, args)
    if 'p_record' in args:
        args['p_record']['source_lineage'] = deepcopy(expectation['lineage'])
    elif 'p_expected_record' in args:
        # This change is deliberately a coherent server expectation rather
        # than rejection by the earlier preview-lineage comparison.
        _update(db, 'UPDATE public.piece_records SET source_lineage=$2::jsonb WHERE id=$1',
            [args['p_preview_id'], json.dumps(expectation['lineage'])])
        if 'p_expected_record' in args:
            args['p_expected_record']['source_lineage'] = deepcopy(expectation['lineage'])
    elif expectation['lineage'] != case['expected']['lineage']:
        _update(db, 'UPDATE public.piece_records SET source_lineage=$2::jsonb WHERE id=$1',
            [args['p_preview_id'], json.dumps(expectation['lineage'])])


@pytest.mark.parametrize('operation', ['issue','visual','save'])
@pytest.mark.parametrize('change', ['target_is_current','duplicate_excerpt','receipt_stage',
    'context_digest','needs_detail','finish_before_observation','metadata_digest','explanation_digest'])
def test_all_writers_reject_coherent_correction_corruption(corrected_sql_db, monkeypatch, operation, change):
    db = corrected_sql_db
    case = _case(db, monkeypatch)
    args = (_issue_args(case) if operation=='issue' else
        _mutation_args(db, case, case['issued']) if operation=='visual' else _saved_args(case, case['issued']))
    assert 'code' not in db.query('BEGIN')
    try:
        _coherent_change(db, case, args, change)
        before = _piece_state(db)
        result = rpc(db, {'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2',
            'save':'piece_save_v2'}[operation], args)
        assert result == {'code':'P0001','message':'PIECE_CONFLICT'}, result
        assert _piece_state(db) == before
    finally:
        assert 'code' not in db.query('ROLLBACK')


@pytest.mark.parametrize('operation', ['issue','visual','save'])
@pytest.mark.parametrize('change', ['missing','single_checkpoint','all_checkpoints'])
def test_corrected_stage_requires_its_own_exclusive_expectation(corrected_sql_db, monkeypatch, operation, change):
    db = corrected_sql_db
    case = _case(db, monkeypatch)
    args = (_issue_args(case) if operation=='issue' else
        _mutation_args(db, case, case['issued']) if operation=='visual' else _saved_args(case, case['issued']))
    expected = args['p_expected_source_state']
    if change=='missing':
        del expected['interpretation_correction']
    elif change=='single_checkpoint':
        expected['meaning_checkpoint'] = {}
    else:
        expected['meaning_checkpoints'] = []
    before = _piece_state(db)
    result = rpc(db, {'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2',
        'save':'piece_save_v2'}[operation], args)
    assert result == {'code':'P0001','message':'PIECE_REQUEST_INVALID'}, result
    assert _piece_state(db) == before


@pytest.mark.parametrize('operation', ['issue','visual','save'])
def test_existing_answer_stage_rejects_correction_expectation(corrected_sql_db, monkeypatch, operation):
    db = corrected_sql_db
    case = _answer_case(prepare_answer_update(db, monkeypatch, 'ADD'))
    issued = rpc(db, 'piece_issue_preview_v2', _issue_args(case))
    assert 'code' not in issued, issued
    args = (_issue_args(case) if operation=='issue' else
        _mutation_args(db, case, issued) if operation=='visual' else _saved_args(case, issued))
    args['p_expected_source_state']['interpretation_correction'] = {}
    before = _piece_state(db)
    result = rpc(db, {'issue':'piece_issue_preview_v2','visual':'piece_mutate_preview_visual_v2',
        'save':'piece_save_v2'}[operation], args)
    assert result == {'code':'P0001','message':'PIECE_REQUEST_INVALID'}, result
    assert _piece_state(db) == before


@pytest.mark.parametrize('update', ['ADD','REVISE'])
def test_previous_source_states_keep_all_three_writer_paths(corrected_sql_db, monkeypatch, update):
    db = corrected_sql_db
    case = _answer_case(prepare_answer_update(db, monkeypatch, update))
    expected_keys = {'original','thread_id','thread_revision','lineage'}
    if update=='REVISE':
        expected_keys.add('meaning_checkpoint')
    assert set(case['expected']) == expected_keys
    issued = rpc(db, 'piece_issue_preview_v2', _issue_args(case))
    assert 'code' not in issued, issued
    visual = rpc(db, 'piece_mutate_preview_visual_v2', _mutation_args(db, case, issued))
    assert 'code' not in visual, visual
    saved = rpc(db, 'piece_save_v2', _saved_args(case, visual))
    assert 'code' not in saved, saved
