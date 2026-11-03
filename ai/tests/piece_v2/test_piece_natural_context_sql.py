"""Actual Piece RPC SQL on disposable PGlite, with synthetic Auth/provider.

This checks the natural saved-cohort boundary, not native concurrency, GPU,
real-user content, device rendering or product quality.
"""
import json
import os
from pathlib import Path
import runpy
from uuid import uuid4

import pytest

from test_emlis_q3_application import Q3Database
from test_emlis_q2_application import run
from test_emlis_natural_reply_application import natural_case, _piece_adapter
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe

ROOT = Path(__file__).parents[3]
B2 = runpy.run_path(str(Path(__file__).parent / 'db/test_b02_piece_v2_foundation.py'))


def script(db, sql):
    with db.lock:
        db.proc.stdin.write(json.dumps({'sql': sql, 'script': True}) + '\n')
        db.proc.stdin.flush()
        result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result


@pytest.fixture(scope='module')
def qdb():
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('PostgreSQL WASM dependency not configured')
    db = Q3Database()
    db.migrate()
    columns = ','.join(c.split()[0] for c in B2['_LEGACY_COLUMNS'])
    script(db, 'create table public.mymodel_reflections (' + ','.join(B2['_LEGACY_COLUMNS']) + ');'
        + 'create view public.pieces with (security_invoker=true) as select ' + columns + ' from public.mymodel_reflections;'
        + 'revoke all on public.pieces from public,anon,authenticated; grant select on public.pieces to service_role;')
    for name in ['20260808_001_piece_v2_legacy_read_bridge.sql', '20260808_002_piece_v2_foundation.sql',
                 '20260808_003_piece_v2_rls_and_staging.sql', '20260808_004_piece_v2_atomic_functions.sql',
                 '20261010050940_piece_v2_preview_visual_change.sql', '20261101022630_piece_natural_reply_context.sql',
                 '20261103235434_piece_v2_expand_visual_palette.sql']:
        script(db, (ROOT / 'supabase/migrations' / name).read_text())
    yield db
    db.proc.stdin.close()
    db.proc.wait(timeout=10)


def rpc(db, name, payload, *, expected_failure=False):
    args = ','.join(f'{key} => ${i}' for i, key in enumerate(payload, 1))
    params = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in payload.values()]
    result = db.query(f'select public.{name}({args}) as value', params, 'service_role')
    if expected_failure:
        assert result.get('code') == 'P0001', result
        return None
    assert 'code' not in result, result
    return result['rows'][0]['value']


@pytest.mark.parametrize('tier,days', [('free', 1), ('plus', 200), ('premium', 4000)])
@pytest.mark.parametrize('invalidated', [False, True])
def test_natural_saved_cohort_survives_preview_visual_and_save(natural_case, qdb, monkeypatch, tier, days, invalidated):
    import hashlib
    user, parent, service, calls = natural_case
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    past = str(uuid4())
    qdb.query("insert into public.emotions values ($1,$2,(now()-($3||' days')::interval) at time zone 'UTC',$4,'',array['仕事'],array['平穏'],$5)",
        [past, user, str(days), '会議の資料を読み直した。', json.dumps([dict(type='平穏', strength='medium')])])
    run(service.start(user, parent))
    adapter = _piece_adapter(user, service, monkeypatch)
    handoff = run(adapter.resolve_original_handoff('Bearer synthetic', parent))
    lineage = handoff.lineage_payload()
    expected = {'original': handoff.original.original_payload(), 'thread_id': handoff.thread_id,
                'thread_revision': handoff.thread_revision, 'lineage': lineage}
    # Add newer records after generation: they must not replace the saved cohort.
    for _ in range(4):
        qdb.query("insert into public.emotions values ($1,$2,(now()-interval '1 hour') at time zone 'UTC',$3,'',array['仕事'],array['平穏'],$4)",
            [str(uuid4()), user, '会議の資料を読み直した。', json.dumps([dict(type='平穏', strength='medium')])])
    generated = run(adapter.generate_original_candidate_from_saved_state('Bearer synthetic', parent))
    candidate = generated['candidate']
    assert generated['source_lineage'] == lineage
    assert candidate['piece_text'] == '会議の資料を読み直した。終わって少し安心した。'
    recipe = build_visual_recipe(candidate['format_type'], tier=tier, language='ja')
    record = {k: candidate[k] for k in ['format_type', 'content_payload', 'piece_text', 'piece_text_hash']}
    record.update(content_payload_hash=canonical_sha256_hex(candidate['content_payload']),
                  safety_state='ready', renderer_version='piece.rn_bitmap_renderer.ios.v1')
    record.update(source_lineage=lineage, visual_recipe=recipe,
                  visual_recipe_hash=canonical_sha256_hex(recipe), eligible_formats=candidate['eligible_formats'])
    issued = rpc(qdb, 'piece_issue_preview_v2', {'p_owner_user_id': user,
        'p_idempotency_key_hash': hashlib.sha256(('preview-' + parent).encode()).hexdigest(),
        'p_request_hash': canonical_sha256_hex(record), 'p_record': record,
        'p_ttl_seconds': 600, 'p_expected_subscription_tier': tier, 'p_expected_source_state': expected})
    row = qdb.query('select to_jsonb(r) as r from public.piece_records r where id=$1', [issued['preview_id']])['rows'][0]['r']
    keys = ['id','owner_user_id','piece_contract_version','lifecycle_status','preview_request_hash',
        'preview_revision','row_version','expires_at','visibility_scope','source_lineage','format_type',
        'preview_eligible_formats','content_payload','content_payload_hash','piece_text','piece_text_hash',
        'safety_state','visual_recipe','visual_recipe_hash','renderer_version']
    changed_recipe = build_visual_recipe(candidate['format_type'], tier=tier, language='ja',
        theme={'free': 'soft_paper', 'plus': 'rose_berry', 'premium': 'ocean_ice'}[tier])
    visual_args = {'p_owner_user_id': user,
        'p_preview_id': issued['preview_id'], 'p_expected_preview_revision': 1,
        'p_expected_record': {k: row[k] for k in keys}, 'p_visual_recipe': changed_recipe,
        'p_visual_recipe_hash': canonical_sha256_hex(changed_recipe),
        'p_expected_subscription_tier': tier, 'p_expected_source_state': expected}
    save_args = {'p_owner_user_id': user, 'p_preview_id': issued['preview_id'],
        'p_expected_preview_revision': 1, 'p_piece_text_hash': record['piece_text_hash'],
        'p_content_payload_hash': record['content_payload_hash'], 'p_visual_recipe_hash': record['visual_recipe_hash'],
        'p_idempotency_key_hash': hashlib.sha256(('save-' + parent).encode()).hexdigest(),
        'p_visibility_scope': 'private', 'p_expected_subscription_tier': tier, 'p_expected_source_state': expected}
    if invalidated:
        target = parent if tier == 'free' else past
        if tier == 'premium':
            qdb.query('delete from public.emotions where id=$1', [target])
        else:
            qdb.query("update public.emotions set memo='変更された記録' where id=$1", [target])
        rpc(qdb, 'piece_mutate_preview_visual_v2', visual_args, expected_failure=True)
        rpc(qdb, 'piece_save_v2', save_args, expected_failure=True)
        rpc(qdb, 'piece_issue_preview_v2', {'p_owner_user_id': user,
            'p_idempotency_key_hash': hashlib.sha256(('second-' + parent).encode()).hexdigest(),
            'p_request_hash': canonical_sha256_hex(record), 'p_record': record, 'p_ttl_seconds': 600,
            'p_expected_subscription_tier': tier, 'p_expected_source_state': expected}, expected_failure=True)
        assert qdb.query('select count(*) as n from public.piece_quota_consumptions where owner_user_id=$1', [user])['rows'][0]['n'] == 0
        return
    changed = rpc(qdb, 'piece_mutate_preview_visual_v2', visual_args)
    save_args['p_expected_preview_revision'] = changed['preview_revision']
    save_args['p_visual_recipe_hash'] = changed['visual_recipe_hash']
    saved = rpc(qdb, 'piece_save_v2', save_args)
    assert saved['lifecycle_status'] == 'saved'
    reread = qdb.query('select piece_text,piece_text_hash,content_payload,visibility_scope,visual_recipe,visual_recipe_hash from public.piece_records where id=$1', [saved['piece_id']])['rows'][0]
    assert all(reread[k] == record[k] for k in ['piece_text', 'piece_text_hash', 'content_payload'])
    assert reread['visual_recipe'] == changed_recipe
    assert reread['visual_recipe_hash'] == canonical_sha256_hex(changed_recipe)
    assert reread['visibility_scope'] == 'private'
    assert len(calls) == 1
    assert qdb.query('select count(*) as n from public.piece_quota_consumptions where owner_user_id=$1', [user])['rows'][0]['n'] == 1


def test_context_migration_preserves_service_only_function_privileges(qdb):
    result = qdb.query("select proname,prosecdef,proconfig, has_function_privilege('anon',p.oid,'execute') as anon_exec, has_function_privilege('authenticated',p.oid,'execute') as auth_exec,has_function_privilege('service_role',p.oid,'execute') as service_exec from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('piece_issue_preview_v2','piece_save_v2','piece_mutate_preview_visual_v2') and 'p_expected_source_state'=any(p.proargnames)")
    assert len(result['rows']) == 3
    for row in result['rows']:
        assert row['prosecdef'] and row['proconfig'] == ['search_path=pg_catalog']
        assert row['service_exec'] and not row['anon_exec'] and not row['auth_exec']
