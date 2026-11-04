"""Actual Piece RPC SQL on disposable PGlite, with synthetic Auth/provider.

This checks the natural saved-cohort boundary, not native concurrency, GPU,
real-user content, device rendering or product quality.
"""
import json
import os
from pathlib import Path
import runpy
from uuid import uuid4

import httpx
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
                 '20261103235434_piece_v2_expand_visual_palette.sql', '20261010_005_piece_v2_quota_read.sql']:
        script(db, (ROOT / 'supabase/migrations' / name).read_text())
    yield db
    db.proc.stdin.close()
    db.proc.wait(timeout=10)


def rpc_query(db, name, payload):
    args = ','.join(f'{key} => ${i}' for i, key in enumerate(payload, 1))
    params = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in payload.values()]
    return db.query(f'select public.{name}({args}) as value', params, 'service_role', error_message=True)


def rpc(db, name, payload, *, expected_failure=False):
    result = rpc_query(db, name, payload)
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


@pytest.fixture
def format_flow(natural_case, qdb, monkeypatch):
    import api_piece_v2 as api
    import piece_v2_preview_service as preview_service
    import piece_v2_save_service as save_service
    import piece_v2_safety_review as safety_review
    import supabase_client
    from piece_v2_runtime_control import create_piece_preview_application

    user, parent, service, provider_calls = natural_case
    state = {'lost_issue_ack': False, 'issued': [], 'reviews': [], 'provider_calls': provider_calls}

    async def verify(authorization):
        assert authorization == 'Bearer synthetic'
        return user

    async def post(name, args, *, timeout):
        assert timeout == 8.0
        result = rpc_query(qdb, name, args)
        if 'code' in result:
            return httpx.Response(400, json=result)
        payload = result['rows'][0]['value']
        if name == 'piece_issue_preview_v2':
            state['issued'].append(payload['preview_id'])
            if state['lost_issue_ack']:
                state['lost_issue_ack'] = False
                raise TimeoutError()
        return httpx.Response(200, json=payload)

    async def get(path, *, params, timeout):
        assert path == '/rest/v1/piece_records' and timeout == 8.0
        where = ['id=$1', 'owner_user_id=$2']
        values = [params['id'][3:], params['owner_user_id'][3:]]
        if params.get('lifecycle_status') == 'eq.saved':
            where.append("lifecycle_status='saved'")
        theme_key = 'visual_recipe->theme->>theme_id'
        if theme_key in params:
            assert params[theme_key] == 'in.(soft_paper,quiet_night)'
            where.append("visual_recipe->'theme'->>'theme_id' in ($3,$4)")
            values.extend(['soft_paper', 'quiet_night'])
        result = qdb.query('select to_jsonb(r) as value from public.piece_records r '
            + 'where ' + ' and '.join(where), values, 'service_role')
        assert 'code' not in result, result
        records = [row['value'] for row in result['rows']]
        columns = params['select'].split(',')
        return httpx.Response(200, json=[{key: row[key] for key in columns} for row in records])

    actual_review = safety_review.review_prepared_original

    async def review(candidate):
        state['reviews'].append(candidate.artifact_payload()['format_type'])
        return await actual_review(candidate)

    monkeypatch.setattr(api, '_verify_bearer', verify)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', post)
    monkeypatch.setattr(supabase_client, 'sb_get', get)
    monkeypatch.setattr(safety_review, 'review_prepared_original', review)
    app = create_piece_preview_application(preview_requested=True, preview_ready=True,
        preview_runtime={'ttl_seconds': 600, 'renderer_version': 'piece.rn_bitmap_renderer.ios.v1'},
        save_requested=True, save_ready=True, owner_read_requested=True, owner_read_ready=True)

    def prepare(tier):
        qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
        qdb.query('update public.emotions set memo=$2 where id=$1', [parent,
            '私が大切にしたいのは、家族と落ち着いてゆっくり話す時間です。'])
        run(service.start(user, parent))
        adapter = _piece_adapter(user, service, monkeypatch)
        monkeypatch.setattr(preview_service, 'PieceSavedSourceAdapter', lambda: adapter)
        monkeypatch.setattr(save_service, 'PieceSavedSourceAdapter', lambda: adapter)
        return {'source_ref': run(adapter.resolve_original_source_ref('Bearer synthetic', parent)),
            'requested_format': None,
            'visual_selection': {'theme_id': None, 'aspect_ratio': None, 'branding_mode': None}}

    async def call(method, path, value=None, *, key=None, expanded=True):
        headers = {'Authorization': 'Bearer synthetic', 'X-Piece-Renderer': 'piece.rn_bitmap_renderer.ios.v2'}
        if expanded:
            headers['X-Piece-Palette'] = '2'
        if key:
            headers['Idempotency-Key'] = key
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url='https://test.invalid') as client:
            return await client.request(method, '/emotion/piece/' + path, headers=headers, json=value)

    return prepare, call, state, user


def _save_body(preview):
    return {'preview_id': preview['preview_id'], 'expected_preview_revision': preview['preview_revision'],
        **{key: preview[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')}}


@pytest.mark.parametrize('lose_ack,old_expires', [(False, False), (True, False), (False, True)])
def test_premium_format_replacement_uses_distinct_drafts_and_keeps_visual_choice(
        format_flow, qdb, lose_ack, old_expires):
    from piece_v2_visual import THEME_IDS

    prepare, call, state, user = format_flow
    request = prepare('premium')
    initial = run(call('POST', 'preview', request, key='initial-format'))
    assert initial.status_code == 200, initial.json()
    first = initial.json()
    assert set(first['eligible_formats']) >= {'short_essay', 'quote'}
    assert first['plan_capabilities']['theme_ids'] == list(THEME_IDS)

    visual = {'theme_id': 'rose_berry', 'aspect_ratio': '9:16', 'branding_mode': 'off'}
    changed = run(call('PATCH', 'preview/' + first['preview_id'], {
        'expected_preview_revision': first['preview_revision'], 'visual_selection': visual}))
    assert changed.status_code == 200, changed.json()
    previous = changed.json()
    assert previous['piece_text_hash'] == first['piece_text_hash']
    assert previous['preview_revision'] == 2
    chosen = next(fmt for fmt in previous['eligible_formats'] if fmt != previous['format_type'])
    replacement = dict(request, requested_format=chosen, visual_selection=visual)
    conflict = run(call('POST', 'preview', replacement, key='initial-format'))
    assert conflict.status_code == 409 and conflict.json() == {'code': 'PIECE_CONFLICT'}

    state['lost_issue_ack'] = lose_ack
    result = run(call('POST', 'preview', replacement, key='replacement-format'))
    if lose_ack:
        assert result.status_code == 503 and result.json() == {'code': 'PIECE_TEMPORARILY_UNAVAILABLE'}
        old = run(call('POST', 'preview', request, key='initial-format'))
        assert old.status_code == 200 and old.json() == previous
        result = run(call('POST', 'preview', replacement, key='replacement-format'))
    assert result.status_code == 200, result.json()
    latest = result.json()
    assert latest['preview_id'] != previous['preview_id'] and latest['preview_revision'] == 1
    assert latest['format_type'] == latest['content_payload']['format_type'] == chosen
    assert latest['content_payload_hash'] != previous['content_payload_hash']
    assert latest['visual_recipe']['theme']['theme_id'] == visual['theme_id']
    assert latest['visual_recipe']['aspect_ratio'] == visual['aspect_ratio']
    assert latest['visual_recipe']['branding']['branding_mode'] == visual['branding_mode']
    assert latest['quota']['saved_count'] == 0
    assert len(state['provider_calls']) == 1
    assert state['issued'] == [previous['preview_id'], latest['preview_id']]
    assert state['reviews'] == [first['format_type'], previous['format_type'], chosen]

    old_rows = qdb.query('select id, lifecycle_status from public.piece_records where owner_user_id=$1',
        [user])['rows']
    assert {row['id'] for row in old_rows if row['lifecycle_status'] == 'preview_draft'} == set(state['issued'])
    if old_expires:
        expired = qdb.query("update public.piece_records set expires_at=clock_timestamp()-interval '1 second' "
            'where id=$1 returning id', [previous['preview_id']])
        assert expired['rows'] == [{'id': previous['preview_id']}]
    cancel = run(call('DELETE', 'preview/' + previous['preview_id'],
        {'expected_preview_revision': previous['preview_revision']}))
    old_error = 'PIECE_PREVIEW_EXPIRED' if old_expires else 'PIECE_CONFLICT'
    if old_expires:
        assert cancel.status_code == 409 and cancel.json() == {'code': old_error}
    else:
        assert cancel.status_code == 200 and cancel.json()['lifecycle_status'] == 'cancelled'
    old_save = run(call('POST', 'save', _save_body(previous), key='old-save'))
    assert old_save.status_code == 409 and old_save.json() == {'code': old_error}

    saved = run(call('POST', 'save', _save_body(latest), key='selected-save'))
    assert saved.status_code == 200 and saved.json()['piece_id'] == latest['preview_id']
    detail = run(call('GET', latest['preview_id']))
    assert detail.status_code == 200, detail.json()
    legacy_detail = run(call('GET', latest['preview_id'], expanded=False))
    assert legacy_detail.status_code == 404 and legacy_detail.json() == {'code': 'PIECE_NOT_FOUND'}
    for field in ('format_type', 'piece_text', 'piece_text_hash', 'content_payload_hash',
                  'visual_recipe', 'visual_recipe_hash'):
        assert detail.json()[field] == latest[field]
    assert qdb.query('select count(*) as n from public.piece_quota_consumptions where owner_user_id=$1',
        [user])['rows'][0]['n'] == 1


@pytest.mark.parametrize('tier', ['free', 'plus'])
def test_nonpremium_cannot_issue_a_requested_format(format_flow, qdb, tier):
    prepare, call, state, user = format_flow
    request = prepare(tier)
    ordinary = run(call('POST', 'preview', request, key='ordinary-format'))
    assert ordinary.status_code == 200, ordinary.json()
    assert 'quote' in ordinary.json()['eligible_formats']
    denied = run(call('POST', 'preview', dict(request, requested_format='quote'), key='picked-format'))
    assert denied.status_code == 422 and denied.json() == {'code': 'PIECE_FORMAT_NOT_ELIGIBLE'}
    assert state['issued'] == [ordinary.json()['preview_id']]
    assert qdb.query('select count(*) as n from public.piece_quota_consumptions where owner_user_id=$1',
        [user])['rows'][0]['n'] == 0
