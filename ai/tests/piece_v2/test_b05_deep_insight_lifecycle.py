"""Verify the distinct typed source across the existing Piece write owners."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from uuid import uuid4

import pytest

from test_analysis_deep_insight_handoff import RECEIVED_MAP_MIGRATIONS
from test_b05_answer_correction_sql_fence import revised_frame_db, recovered_natural_db, mixed_fence_db
from test_b05_interpretation_correction_application import corrected_db
from test_b05_effective_round_sql_fence import effective_fence_db, _apply
from test_b05_natural_refined_saved_pipeline import natural_refined_db, refined_pipeline_db, saved_piece_db
from test_b05_refined_source_fence_sql import _RECORD, _case, _issue_args, _mutation_args, _saved_args, rpc
from test_piece_deep_insight_source_binding import MIGRATION, read, selection


LIFECYCLE_MIGRATION = '20261128061355_piece_deep_insight_lifecycle.sql'
ISSUE = 'piece_issue_preview_v2'
VISUAL = 'piece_mutate_preview_visual_v2'
SAVE = 'piece_save_v2'


@pytest.fixture(scope='module')
def piece_db(revised_frame_db):
    db = revised_frame_db
    assert 'code' not in db.query('alter table public.emotions add column is_secret boolean not null default false')
    for migration in (*RECEIVED_MAP_MIGRATIONS, '20261121134000_deep_insight_grounded_questions.sql',
                      MIGRATION, LIFECYCLE_MIGRATION):
        _apply(db, migration)
    return db


def typed_case(db, selection):
    owner, _, source, question, _ = selection
    binding = read(db, owner, source, question)
    original = binding['original']
    recorded_at = datetime.fromisoformat(original['created_at']).replace(tzinfo=timezone.utc).isoformat()
    lineage = {
        'handoff_contract_version': 'cocolon.cross_core.source_handoff.v1',
        'piece_source_lineage_version': 'piece.source_lineage.v1',
        'source_kind': 'deep_insight_record_answer',
        'semantic_source_roles': ['original_input', 'deep_insight_answer'],
        'body_free': True,
        'source_input': {
            'source_input_id': source,
            'source_input_version': 'emlis.current_input_bundle.v1',
            'source_input_bundle_commitment': 'sha256:' + 'c' * 64,
            'source_owner_user_id': owner,
            'source_recorded_at': recorded_at,
        },
        'deep_insight': {
            'deep_insight_question_id': question,
            'source_version': binding['source_version'],
            'source_commitment': binding['commitment'],
        },
    }
    record = _RECORD()
    record['source_lineage'] = lineage
    return dict(owner=owner, record=record, expected=dict(original=original, lineage=lineage))


def test_typed_piece_issues_changes_visual_and_saves_one_snapshot(piece_db, selection):
    db = piece_db
    case = typed_case(db, selection)
    issue_args = _issue_args(case)
    issued = rpc(db, ISSUE, issue_args)
    assert issued.get('preview_revision') == 1, issued
    replay = rpc(db, ISSUE, issue_args)
    assert replay['idempotency_replayed'] and replay['preview_id'] == issued['preview_id']
    mutated = rpc(db, VISUAL, _mutation_args(db, case, issued))
    assert mutated.get('preview_revision') == 2, mutated
    save_args = _saved_args(case, issued | mutated)
    saved = rpc(db, SAVE, save_args)
    assert saved['lifecycle_status'] == 'saved' and saved['visibility_scope'] == 'private'

    owner, _, source, _, _ = selection
    db.query('update public.emotions set is_secret=true where id=$1', [source])
    db.query("update public.profiles set subscription_tier='free' where id=$1", [owner])
    assert read(db, owner, source, selection[3]) is None
    # Repeating a completed save reads the same saved identity after revocation.
    replay = rpc(db, SAVE, save_args | {'p_replay_only': True, 'p_expected_source_state': None})
    assert replay == saved | {'idempotency_replayed': True}
    row = db.query('select source_lineage, piece_text from public.piece_records where id=$1', [saved['piece_id']])['rows'][0]
    assert row == dict(source_lineage=case['record']['source_lineage'], piece_text=issued['piece_text'])


@pytest.mark.parametrize('change', ['secret', 'downgrade', 'changed-answer', 'changed-record', 'unfenced-save'])
def test_typed_draft_does_not_survive_changed_source_or_missing_fence(piece_db, selection, change):
    db = piece_db
    case = typed_case(db, selection)
    issue_args = _issue_args(case)
    issued = rpc(db, ISSUE, issue_args)
    assert issued.get('preview_id'), issued
    owner, _, source, question, _ = selection
    changes = {
        'secret': ('update public.emotions set is_secret=true where id=$1', source),
        'downgrade': ("update public.profiles set subscription_tier='plus' where id=$1", owner),
        'changed-answer': ("update public.deep_insight_questions set answer_text=answer_text||'更新' where id=$1", question),
        'changed-record': ("update public.emotions set memo=memo||'更新' where id=$1", source),
    }
    args = _saved_args(case, issued)
    if change == 'unfenced-save':
        args.update(p_expected_source_state=None, p_expected_subscription_tier=None)
    else:
        sql, parameter = changes[change]
        assert 'code' not in db.query(sql, [parameter])
        assert rpc(db, ISSUE, issue_args).get('message') == 'PIECE_CONFLICT'
        assert rpc(db, VISUAL, _mutation_args(db, case, issued)).get('message') == 'PIECE_CONFLICT'
    assert rpc(db, SAVE, args).get('message') == 'PIECE_CONFLICT'
    row = db.query('select lifecycle_status, preview_revision::integer from public.piece_records where id=$1',
                   [issued['preview_id']])
    assert row['rows'] == [dict(lifecycle_status='preview_draft', preview_revision=1)]
    assert db.query('select 1 from public.piece_quota_consumptions where owner_user_id=$1', [owner])['rows'] == []


def test_five_argument_issue_rejects_an_invalid_typed_selection(piece_db, selection):
    case = typed_case(piece_db, selection)
    args = _issue_args(case)
    args.pop('p_expected_subscription_tier')
    args.pop('p_expected_source_state')
    args['p_record']['source_lineage']['deep_insight']['source_commitment'] = 'sha256:' + 'f' * 64
    assert rpc(piece_db, ISSUE, args).get('message') == 'PIECE_CONFLICT'
    args['p_record'] = deepcopy(case['record'])
    args['p_record']['source_lineage']['observation'] = {}
    assert rpc(piece_db, ISSUE, args).get('message') == 'PIECE_CONFLICT'


def test_expired_typed_draft_cannot_replay_edit_or_save(piece_db, selection):
    case = typed_case(piece_db, selection)
    args = _issue_args(case)
    issued = rpc(piece_db, ISSUE, args)
    assert issued.get('preview_id'), issued
    result = piece_db.query("update public.piece_records set expires_at=clock_timestamp()-interval '1 second' where id=$1",
                            [issued['preview_id']])
    assert 'code' not in result, result
    assert rpc(piece_db, ISSUE, args)['message'] == 'PIECE_PREVIEW_EXPIRED'
    assert rpc(piece_db, VISUAL, _mutation_args(piece_db, case, issued))['message'] == 'PIECE_PREVIEW_EXPIRED'
    assert rpc(piece_db, SAVE, _saved_args(case, issued))['message'] == 'PIECE_PREVIEW_EXPIRED'


def test_existing_emlis_lineage_still_uses_the_three_original_writers(piece_db):
    case = _case(piece_db, '', refined=False)
    assert set(case['expected']) == {'original', 'thread_id', 'thread_revision', 'lineage'}
    issued = rpc(piece_db, ISSUE, _issue_args(case))
    assert issued.get('preview_id'), issued
    mutated = rpc(piece_db, VISUAL, _mutation_args(piece_db, case, issued))
    assert mutated.get('preview_revision') == 2, mutated
    saved = rpc(piece_db, SAVE, _saved_args(case, issued | mutated))
    assert saved.get('lifecycle_status') == 'saved', saved


@pytest.mark.parametrize('prior', ['emlis-answer', 'separate-safety'])
def test_typed_selection_excludes_prior_sources_needing_separate_admission(piece_db, selection, prior):
    db = piece_db
    owner, _, source, question, _ = selection
    original = read(db, owner, source, question)['original']
    thread = str(uuid4())
    data = (dict(body_state='UNAVAILABLE', failure_code='separate_safety_owner_required')
            if prior == 'separate-safety' else dict(body_state='FINAL'))
    inserted = db.query("""insert into public.emlis_input_threads(
        id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
        values($1,$2,$3,1,'COMPLETED',0,$4::jsonb,$5::jsonb)""",
        [thread, owner, source, json.dumps(original), json.dumps(data)])
    assert 'code' not in inserted, inserted
    if prior == 'emlis-answer':
        assert read(db, owner, source, question) is not None
        inserted = db.query("""insert into public.emlis_thread_events(
            id,thread_id,seq,kind,round_index,question_id,payload)
            values($1,$2,1,'ANSWER',1,'earlier-emlis-question','{}'::jsonb)""", [str(uuid4()), thread])
        assert 'code' not in inserted, inserted
    assert read(db, owner, source, question) is None
