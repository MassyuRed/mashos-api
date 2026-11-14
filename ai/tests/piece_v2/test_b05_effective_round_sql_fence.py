"""Effective-round SQL fences over an independent disposable PostgreSQL fixture.

Genuine synthetic Emlis rounds establish the source state. Deliberately altered
checkpoints are structurally coherent SQL expectations, never semantic sources.
No model, hosted database, native runtime or production mutation is exercised.
"""
import asyncio
from copy import deepcopy
import json
from pathlib import Path

import pytest

from cocolon_meaning_experience_engine.emlis_thread_source import identity
from piece_v2_contract import PieceContractError
from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_refined_fence
from test_b05_natural_refined_saved_pipeline import (
    natural_refined_db, refined_pipeline_db, saved_piece_db,
)
from test_b05_piece_answer_update_saved_pipeline import (
    ANSWERS, prepare_answer_update, prepare_later_update,
)
from test_b05_refined_source_fence_sql import (
    SIGNATURES, _catalog, _canonical_lineage, _RECORD, _issue_args,
    _mutation_args, _saved_args, _piece_state, _update, rpc,
)

ROOT = Path(__file__).parents[3]
run = asyncio.run


def _apply(db, filename):
    db.proc.stdin.write(json.dumps(dict(
        sql=(ROOT/'supabase/migrations'/filename).read_text(), script=True))+'\n')
    db.proc.stdin.flush()
    result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result


@pytest.fixture(scope='module')
def effective_fence_db(natural_refined_db):
    db = natural_refined_db
    _apply(db, '20261114051948_piece_natural_answer_active_source.sql')
    _apply(db, '20261114074058_piece_natural_latest_answer_update.sql')
    before = _catalog(db)
    _apply(db, '20261114190006_piece_natural_effective_round_sources.sql')
    db.effective_fence_catalog = (before, _catalog(db))
    return db


def _case(state):
    snapshot = state['snapshot_before']
    thread = snapshot['thread']
    handoff = run(PieceSavedSourceAdapter().resolve_refined_handoff(
        'Bearer '+state['token'], state['source_id'],
        supplemental_answer_identity=thread['latest_answer_event_id'], opted_in=True))
    record = _RECORD()
    record['source_lineage'] = _canonical_lineage(handoff)
    expected = dict(original=state['original'], thread_id=thread['id'],
        thread_revision=thread['revision'], lineage=record['source_lineage'],
        **project_saved_refined_fence(handoff))
    return dict(owner=state['owner'], parent=state['source_id'], snapshot=snapshot,
        token=state['token'], handoff=handoff, record=record, expected=expected)


def test_effective_migration_preserves_catalog_signatures_and_execute_acl(effective_fence_db):
    db = effective_fence_db
    before, after = db.effective_fence_catalog
    assert before == after
    for signature in SIGNATURES:
        for role, expected in [('anon', False), ('authenticated', False), ('service_role', True)]:
            result = db.query('SELECT has_function_privilege($1,$2,\'EXECUTE\') AS allowed',
                [role, signature])
            assert result['rows'][0]['allowed'] is expected


@pytest.mark.parametrize('update', ['ADD', 'REVISE'])
def test_old_four_key_and_single_checkpoint_states_still_reach_all_writers(
        effective_fence_db, monkeypatch, update):
    db = effective_fence_db
    state = prepare_answer_update(db, monkeypatch, update)
    case = _case(state)
    expected_keys = {'original', 'thread_id', 'thread_revision', 'lineage'}
    if update == 'REVISE':
        expected_keys.add('meaning_checkpoint')
    assert set(case['expected']) == expected_keys
    issued = rpc(db, 'piece_issue_preview_v2', _issue_args(case))
    assert 'code' not in issued, issued
    visual = rpc(db, 'piece_mutate_preview_visual_v2', _mutation_args(db, case, issued))
    assert 'code' not in visual, visual
    saved = rpc(db, 'piece_save_v2', _saved_args(case, visual))
    assert 'code' not in saved, saved


def _coherent_invalid_target(checkpoints, target):
    """Keep every prefix array and content identity consistent with the edit.

    Existence and active ownership of the new target deliberately remain false;
    matching the stored payload and echoing it back must not grant that meaning.
    """
    checkpoint = deepcopy(checkpoints[-1])
    answer_update = checkpoint['answer_update']
    item, = answer_update['updates']
    assert item['operation'] == 'WITHDRAW'
    item['target_meaning_refs'] = [target]
    item['superseded_claim_refs'] = [target]
    item['update_ref'] = identity('emlis-update', answer_update['answer_source_ref'],
        tuple(item['evidence_refs']), item['operation'], tuple(item['target_meaning_refs']),
        tuple(item['changed_claim_refs']), item['temporal_binding']['about_time'])
    answer_update['new_meaning_ref'] = identity('emlis-meaning',
        checkpoint['base_meaning_ref'], tuple(answer_update['updates']))
    checkpoint['checkpoint_id'] = identity('emlis-checkpoint', checkpoint['source_prefix_ref'],
        checkpoint['base_meaning_ref'], answer_update)
    checkpoint['accepted_update_refs'] = list(dict.fromkeys([
        *checkpoints[-2]['accepted_update_refs'], item['update_ref']]))
    checkpoint['inactive_claim_refs'] = list(dict.fromkeys([
        *checkpoints[-2]['inactive_claim_refs'], *item['superseded_claim_refs'],
        *item['affected_dependency_refs']]))
    assert item['target_meaning_refs'] == item['superseded_claim_refs']
    assert checkpoint['accepted_update_refs'][-1] == item['update_ref']
    return checkpoint


@pytest.mark.parametrize('operation', ['issue', 'visual', 'save'])
@pytest.mark.parametrize('change', ['missing_key', 'foreign_answer', 'inactive_answer'])
def test_all_writers_reject_absent_or_coherently_invalid_effective_prefix(
        effective_fence_db, monkeypatch, operation, change):
    db = effective_fence_db
    if change == 'missing_key':
        texts = [ANSWERS['REVISE'], ANSWERS['ADD']]
    elif change == 'foreign_answer':
        texts = [ANSWERS['REVISE'], '「私は家族を守りたい」は取り消します。']
    else:
        texts = [ANSWERS['REVISE'],
            '「私は家族を守りたい」ではなく「私は資料を読みたい」です。',
            '「私は資料を読みたい」は取り消します。']
    state, _, _ = prepare_later_update(db, monkeypatch, len(texts), 'ADD',
        'premium', answer_texts=texts)
    case = _case(state)
    assert set(case['expected']) == {'original', 'thread_id', 'thread_revision',
        'lineage', 'meaning_checkpoints'}
    args = _issue_args(case)
    if operation != 'issue':
        preview = rpc(db, 'piece_issue_preview_v2', args)
        assert 'code' not in preview, preview
        args = _mutation_args(db, case, preview) if operation == 'visual' else _saved_args(case, preview)
    assert 'code' not in db.query('BEGIN')
    try:
        expectation = args['p_expected_source_state']
        checkpoints = expectation['meaning_checkpoints']
        if change == 'missing_key':
            del expectation['meaning_checkpoints']
            assert case['expected']['meaning_checkpoints'][-1]['answer_update']['updates'][0]['operation'] == 'ADD'
        else:
            introduced = checkpoints[0]['answer_update']['updates'][0]['changed_claim_refs'][0]
            if change == 'foreign_answer':
                target = 'answer:s999999'
                assert all(target not in cp['inactive_claim_refs'] and all(
                    target not in item['changed_claim_refs'] for item in cp['answer_update']['updates'])
                    for cp in checkpoints[:-1])
            else:
                target = introduced
                assert target in checkpoints[-2]['inactive_claim_refs']
                assert target != checkpoints[-1]['answer_update']['updates'][0]['target_meaning_refs'][0]
            value = _coherent_invalid_target(checkpoints, target)
            event = next(e for e in case['snapshot']['events']
                if e['id'] == case['snapshot']['thread']['current_meaning_event_id'])
            _update(db, 'UPDATE public.emlis_thread_events SET payload=$2::jsonb WHERE id=$1',
                [event['id'], json.dumps(value)])
            checkpoints[-1] = deepcopy(value)
            stored = db.query('SELECT payload FROM public.emlis_thread_events WHERE id=$1', [event['id']])
            assert stored['rows'][0]['payload'] == checkpoints[-1]
            with pytest.raises(PieceContractError):
                run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],
                    state['source_id'], supplemental_answer_identity=case['snapshot']['thread']['latest_answer_event_id'],
                    opted_in=True))
        before = _piece_state(db)
        outcome = rpc(db, {'issue':'piece_issue_preview_v2', 'visual':'piece_mutate_preview_visual_v2',
            'save':'piece_save_v2'}[operation], args)
        assert outcome == {'code':'P0001', 'message':'PIECE_CONFLICT'}, outcome
        assert _piece_state(db) == before
    finally:
        assert 'code' not in db.query('ROLLBACK')
