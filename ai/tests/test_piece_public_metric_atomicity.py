"""Legacy public metrics: real isolated SQL and overlapping authenticated calls.

PGlite verifies the actual RPC, ACL and rollback. It serializes SQL requests;
the overlapping HTTP tests independently force the old read/modify/write race.
No live database, real account, V2 public activation or native concurrency claim.
"""
import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_piece_runtime as api
import piece_public_read_store as public_store
import piece_public_read_service as public_service
from test_emlis_q2_application import Database, run


ROOT = Path(__file__).parents[2]


@pytest.fixture(scope='module')
def sql_db():
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained PostgreSQL WASM runtime required'
    db = Database()
    sql = '''create table public.mymodel_qna_metrics(
        q_key text not null, views bigint not null default 0,
        resonances bigint not null default 0, updated_at timestamptz not null default now(),
        q_instance_id text);
        create unique index mymodel_qna_metrics_unique_global on public.mymodel_qna_metrics(q_key)
            where q_instance_id is null;
        create unique index mymodel_qna_metrics_unique_instance on public.mymodel_qna_metrics(q_instance_id)
            where q_instance_id is not null;
        grant select,insert,update on public.mymodel_qna_metrics to service_role;'''
    migrations = sorted((ROOT / 'supabase/migrations').glob('*_piece_legacy_metrics_atomic.sql'))
    assert len(migrations) == 1, 'exactly one canonical legacy metric migration is required'
    sql += migrations[0].read_text()
    with db.lock:
        db.proc.stdin.write(json.dumps({'sql': sql, 'script': True}) + '\n')
        db.proc.stdin.flush()
        result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result
    yield db
    db.proc.stdin.close()
    db.proc.wait(timeout=10)


def sql_rpc(db, key, iid, field='views', delta=1, role='service_role'):
    return db.query('select public.piece_increment_legacy_metric($1,$2,$3,$4) as value',
                    [key, iid, field, delta], role, error_message=True)


@pytest.mark.parametrize('field', ['views', 'resonances'])
def test_sql_counters_preserve_other_field_and_clamp_at_zero(sql_db, field):
    key, iid = 'counter-' + field, 'reflection:counter-' + field
    other = 'resonances' if field == 'views' else 'views'
    assert sql_rpc(sql_db, key, iid, field, -1)['rows'][0]['value'] == {
        'views': 0, 'resonances': 0, 'global_views': 0, 'global_resonances': 0}
    for expected in (1, 2):
        row = sql_rpc(sql_db, key, iid, field)['rows'][0]['value']
        assert row[field] == row['global_' + field] == expected
        assert row[other] == row['global_' + other] == 0
    row = sql_rpc(sql_db, key, iid, field, -1)['rows'][0]['value']
    assert row[field] == row['global_' + field] == 1


def test_global_only_uses_existing_null_instance_identity(sql_db):
    assert sql_rpc(sql_db, 'global-only', None)['rows'] == [
        {'value': {'views': 1, 'resonances': 0}}]
    assert sql_rpc(sql_db, 'global-only', None)['rows'] == [
        {'value': {'views': 2, 'resonances': 0}}]
    assert sql_db.query("select count(*)::int as n from public.mymodel_qna_metrics "
                        "where q_key='global-only'")['rows'] == [{'n': 1}]


@pytest.mark.parametrize('key,iid,field,delta', [
    ('', 'reflection:x', 'views', 1), ('x', '', 'views', 1),
    ('x', None, 'updated_at', 1), ('x', None, 'views', 0),
    ('x', None, 'views', 2), ('x', None, None, 1),
])
def test_invalid_rpc_cannot_write(sql_db, key, iid, field, delta):
    before = sql_db.query('select count(*)::int as n from public.mymodel_qna_metrics')
    assert sql_rpc(sql_db, key, iid, field, delta)['code'] == 'P0001'
    assert sql_db.query('select count(*)::int as n from public.mymodel_qna_metrics') == before


def test_instance_key_conflict_rolls_back_global_increment(sql_db):
    sql_rpc(sql_db, 'original-key', 'reflection:bound')
    result = sql_rpc(sql_db, 'forged-key', 'reflection:bound')
    assert result['code'] == 'P0001' and result['message'] == 'PIECE_METRIC_INSTANCE_KEY_CONFLICT'
    assert sql_db.query("select q_key,views from public.mymodel_qna_metrics "
                        "where q_instance_id='reflection:bound'")['rows'] == [
                            {'q_key': 'original-key', 'views': 1}]
    assert sql_db.query("select count(*)::int as n from public.mymodel_qna_metrics "
                        "where q_key='forged-key'")['rows'] == [{'n': 0}]


def test_rpc_is_service_only_without_definer_privilege(sql_db):
    row = sql_db.query("select prosecdef,proconfig,"
        "has_function_privilege('anon',p.oid,'execute') as anon_exec,"
        "has_function_privilege('authenticated',p.oid,'execute') as auth_exec,"
        "has_function_privilege('service_role',p.oid,'execute') as service_exec "
        "from pg_proc p where p.oid="
        "'public.piece_increment_legacy_metric(text,text,text,integer)'::regprocedure")['rows'][0]
    assert row == dict(prosecdef=False, proconfig=['search_path=pg_catalog'],
                       anon_exec=False, auth_exec=False, service_exec=True)
    for role in ('anon', 'authenticated'):
        assert sql_rpc(sql_db, 'denied', None, role=role)['code'] == '42501'


@pytest.fixture(params=['runtime', 'public_store'])
def metric_helper(request):
    if request.param == 'runtime':
        return api, api._inc_metric, '_sb_post_rpc', '_sb_get', '_sb_patch'
    return public_store, public_store.inc_metric, '_sb_post_rpc_shared', 'sb_get', '_sb_patch_shared'


def test_overlapping_helper_calls_use_one_atomic_rpc_each(sql_db, monkeypatch, metric_helper):
    module, helper, rpc_name, get_name, patch_name = metric_helper
    key, iid = 'overlap-' + module.__name__, 'reflection:overlap-' + module.__name__
    sql_db.query('insert into public.mymodel_qna_metrics(q_key,q_instance_id,views,resonances) '
                 'values ($1,null,10,3),($1,$2,10,3)', [key, iid])
    rpc_calls = []

    async def forbidden(*args, **kwargs):
        raise AssertionError('stale GET/absolute PATCH must not run')

    async def rpc(name, payload, **kwargs):
        assert name == 'piece_increment_legacy_metric'
        assert kwargs == ({'timeout': 8.0} if module is public_store else {})
        rpc_calls.append(dict(payload))
        await asyncio.sleep(0)  # Both helpers enter before either SQL result.
        result = await asyncio.to_thread(sql_rpc, sql_db, payload['p_q_key'],
            payload['p_q_instance_id'], payload['p_field'], payload['p_delta'])
        assert 'code' not in result, result
        return httpx.Response(200, json=result['rows'][0]['value'])

    monkeypatch.setattr(module, get_name, forbidden)
    monkeypatch.setattr(module, patch_name, forbidden)
    monkeypatch.setattr(module, rpc_name, rpc)
    monkeypatch.setattr(module, 'METRICS_TABLE', 'mymodel_qna_metrics')

    async def both():
        return await asyncio.gather(*(helper(q_key=key, q_instance_id=iid,
                                  field='views') for _ in range(2)))
    results = run(both())
    assert sorted(result['views'] for result in results) == [11, 12]
    assert len(rpc_calls) == 2
    assert sql_db.query('select views,resonances from public.mymodel_qna_metrics '
                        'where q_key=$1', [key])['rows'] == [
                            {'views': 12, 'resonances': 3}, {'views': 12, 'resonances': 3}]


@pytest.mark.parametrize('status,payload', [
    (500, {}), (200, {}), (200, []),
    (200, {'views': True, 'resonances': 0}),
    (200, {'views': -1, 'resonances': 0}),
])
def test_metric_transport_never_invents_successful_counts(monkeypatch, status, payload, metric_helper):
    module, helper, rpc_name, *_ = metric_helper
    calls = []
    async def rpc(*args, **kwargs):
        calls.append(args)
        return httpx.Response(status, json=payload)
    monkeypatch.setattr(module, rpc_name, rpc)
    with pytest.raises(HTTPException) as error:
        run(helper(q_key='key', field='views'))
    assert error.value.status_code == 502 and len(calls) == 1


def test_metric_override_cannot_silently_update_another_table(monkeypatch, metric_helper):
    module, helper, rpc_name, *_ = metric_helper
    async def forbidden(*args, **kwargs):
        raise AssertionError('unsupported override must not write')
    monkeypatch.setattr(module, 'METRICS_TABLE', 'custom_metrics')
    monkeypatch.setattr(module, rpc_name, forbidden)
    with pytest.raises(HTTPException) as error:
        run(helper(q_key='key', field='views'))
    assert error.value.status_code == 502


@pytest.mark.parametrize('iid', [None, 'reflection:success'])
def test_both_helpers_keep_existing_success_response(monkeypatch, metric_helper, iid):
    module, helper, rpc_name, *_ = metric_helper
    expected = {'views': 12, 'resonances': 3}
    if iid is not None:
        expected.update(global_views=20, global_resonances=5)
    calls = []
    async def rpc(name, payload, **kwargs):
        calls.append((name, payload, kwargs))
        return httpx.Response(200, json=expected)
    monkeypatch.setattr(module, rpc_name, rpc)
    assert run(helper(q_key=' key ', q_instance_id=iid, field='views')) == expected
    assert calls == [('piece_increment_legacy_metric', {
        'p_q_key': 'key', 'p_q_instance_id': iid, 'p_field': 'views', 'p_delta': 1},
        {'timeout': 8.0} if module is public_store else {})]


def test_public_detail_overlap_reaches_actual_store_and_actual_sql(sql_db, monkeypatch):
    key, iid = 'public-detail', 'reflection:public-detail'
    sql_db.query('insert into public.mymodel_qna_metrics(q_key,q_instance_id,views,resonances) '
                 'values ($1,null,10,3),($1,$2,10,3)', [key, iid])
    calls = []
    row = dict(id='public-detail', owner_user_id='owner', question='保存済みの問い', q_key=key)

    async def access(**kwargs):
        assert kwargs == dict(viewer_user_id='viewer', q_instance_id=iid)
        return row

    async def following(**kwargs):
        return {'owner'}

    async def no_resonance(*args, **kwargs):
        return False

    async def noop(*args, **kwargs):
        return None

    async def forbidden(*args, **kwargs):
        raise AssertionError('public detail must not use stale metric GET/PATCH')

    async def read_metrics(path, *, params):
        assert path == '/rest/v1/' + public_store.METRICS_READ_TABLE
        ids = json.loads('[' + params['q_instance_id'][4:-1] + ']')
        marks = ','.join('$' + str(index + 1) for index in range(len(ids)))
        result = sql_db.query('select q_instance_id,q_key,views::int,resonances::int '
            f'from public.mymodel_qna_metrics where q_instance_id in ({marks})', ids)
        return httpx.Response(200, json=result['rows'])

    async def rpc(name, payload, **kwargs):
        assert name == 'piece_increment_legacy_metric' and kwargs == {'timeout': 8.0}
        calls.append(dict(payload))
        await asyncio.sleep(0)
        result = await asyncio.to_thread(sql_rpc, sql_db, payload['p_q_key'],
            payload['p_q_instance_id'], payload['p_field'], payload['p_delta'])
        assert 'code' not in result, result
        return httpx.Response(200, json=result['rows'][0]['value'])

    # Keep public_service.inc_metric untouched: its real import must lead to
    # the real store, not a test replacement of the increment function.
    assert public_service.inc_metric is public_store.inc_metric
    monkeypatch.setattr(public_service, 'resolve_generated_reflection_access', access)
    monkeypatch.setattr(public_service, 'get_public_generated_reflection_text', lambda row: '保存済み本文です。')
    monkeypatch.setattr(public_service, 'fetch_followed_owner_ids', following)
    monkeypatch.setattr(public_service, 'is_resonated', no_resonance)
    monkeypatch.setattr(public_service, 'upsert_read', noop)
    for name in ('enqueue_ranking_board_refresh', 'enqueue_account_status_refresh',
                 'enqueue_global_summary_refresh'):
        monkeypatch.setattr(public_service, name, noop)
    monkeypatch.setattr(public_store, 'sb_get', read_metrics)
    monkeypatch.setattr(public_store, '_sb_patch_shared', forbidden)
    monkeypatch.setattr(public_store, '_sb_post_rpc_shared', rpc)

    async def overlap():
        return await asyncio.gather(*(public_service.build_qna_public_detail_payload(
            viewer_user_id='viewer', q_instance_id=iid, mark_viewed=True) for _ in range(2)))
    responses = run(overlap())
    # A later aggregate read can already see the second admitted view.
    assert all(11 <= result['views'] <= 12 for result in responses)
    assert max(result['views'] for result in responses) == 12
    assert all(result['q_key'] == key and result['body'] == '保存済み本文です。' for result in responses)
    assert calls == [dict(p_q_key=key, p_q_instance_id=iid, p_field='views', p_delta=1)] * 2
    assert sql_db.query('select views,resonances from public.mymodel_qna_metrics '
                        'where q_key=$1', [key])['rows'] == [
                            {'views': 12, 'resonances': 3}, {'views': 12, 'resonances': 3}]


@pytest.fixture
def reaction_app(monkeypatch):
    # RPC response-contract fixture only. Real legacy state, including alias
    # uniqueness and add/remove interleaving, is covered by the SQL route suite.
    state = dict(resonated=False, increments=[], writes=[], viewer='viewer', malformed=False)
    row = {'owner_user_id': 'owner', 'source_type': 'emotion_generated',
           'q_key': 'generated:canonical', 'question': '保存済みの問い',
           'id': 'db-id', 'public_id': 'public-id'}

    async def resolve(token):
        assert token == 'synthetic'
        return state['viewer']

    async def access(**kwargs):
        assert kwargs['q_instance_id'] in ('reflection:db-id', 'reflection:public-id')
        if state.get('denied'):
            raise HTTPException(status_code=404, detail='Reflection not found')
        return row

    async def metrics(*args, **kwargs):
        return {args[0].copy().pop(): dict(views=10, resonances=5)}

    async def following(**kwargs):
        return {'owner'} if not state.get('unfollowed') else set()

    async def rpc(name, payload):
        assert name == 'piece_apply_legacy_reaction'
        assert payload['p_source_id'] == 'db-id'
        assert payload['p_expected_owner'] == 'owner'
        assert payload['p_viewer_id'] == state['viewer']
        assert payload['p_canonical_id'] == 'reflection:public-id'
        assert payload['p_q_key'] == 'generated:canonical'
        state['writes'].append(('RPC', name, dict(payload)))
        await asyncio.sleep(0)
        removing = payload['p_operation'] == 'remove'
        ack = dict(q_instance_id='reflection:public-id', changed_count=0,
                   resonated=not removing, views=10, resonances=5, deleted_echo_activity_dates=[])
        malformed = state['malformed']
        if malformed == 'shape':
            return httpx.Response(200, json={'not': 'an acknowledgement'})
        if malformed == 'json':
            return httpx.Response(200, content=b'{invalid')
        if malformed:
            key, value = {'wrong-id': ('q_instance_id', 'reflection:unrelated'),
                          'negative': ('views', -1), 'boolean': ('changed_count', True)}[malformed]
            ack[key] = value
            return httpx.Response(200, json=ack)
        pair = (state['viewer'], payload['p_canonical_id'])
        existing = state.setdefault('resonance_rows', {pair} if state['resonated'] else set())
        if removing and pair in existing:
            existing.remove(pair)
            ack['changed_count'] = 1
        elif not removing and pair not in existing:
            existing.add(pair)
            ack['changed_count'] = 1
        if ack['changed_count']:
            state['increments'].append(dict(field='resonances', delta=-1 if removing else 1))
        return httpx.Response(200, json=ack)

    async def forbidden(*args, **kwargs):
        raise AssertionError('reaction must use its atomic RPC, not a separate mutation or counter call')

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(api, '_resolve_user_id_from_token', resolve)
    monkeypatch.setattr(api, 'resolve_generated_reflection_access', access)
    monkeypatch.setattr(api, 'get_public_generated_reflection_text', lambda row: '保存済み本文です。')
    monkeypatch.setattr(api, '_fetch_instance_metrics', metrics)
    monkeypatch.setattr(api, '_fetch_followed_owner_ids', following)
    monkeypatch.setattr(api, '_inc_metric', forbidden)
    monkeypatch.setattr(api, '_sb_post', forbidden)
    monkeypatch.setattr(api, '_sb_delete', forbidden)
    monkeypatch.setattr(api, '_sb_post_rpc', rpc)
    for name in ('_upsert_read', 'enqueue_global_snapshot_refresh', 'enqueue_ranking_board_refresh',
                 'enqueue_account_status_refresh', 'enqueue_global_summary_refresh',
                 'enqueue_global_summary_refresh_many'):
        monkeypatch.setattr(api, name, noop)
    app = FastAPI()
    api.register_piece_runtime_routes(app)
    return app, state


async def reaction(app, path, **values):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        return await client.post('/piece/' + path, headers={'Authorization': 'Bearer synthetic'},
                                 json=dict(q_instance_id='reflection:db-id', **values))


@pytest.mark.parametrize('path', ['resonance', 'resonances/submit', 'resonances/delete'])
def test_overlapping_reaction_uses_rpc_acknowledged_state(reaction_app, path):
    app, state = reaction_app
    state['resonated'] = path.endswith('delete')
    async def overlap():
        values = {'strength': 'medium'} if path.endswith('submit') else {}
        return await asyncio.gather(reaction(app, path, **values), reaction(app, path, **values))
    responses = run(overlap())
    assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
    assert len(state['writes']) == 2 and all(kind == 'RPC' for kind, *_ in state['writes'])
    assert len(state['increments']) == 1
    assert state['increments'][0]['field'] == 'resonances'
    assert state['increments'][0]['delta'] == (-1 if path.endswith('delete') else 1)


@pytest.mark.parametrize('path', ['resonance', 'resonances/submit', 'resonances/delete'])
@pytest.mark.parametrize('malformed', ['shape', 'wrong-id', 'negative', 'boolean', 'json'])
def test_active_reaction_rejects_invalid_rpc_ack_without_second_mutation(reaction_app, path, malformed):
    app, state = reaction_app
    state.update(malformed=malformed, resonated=path.endswith('delete'))
    response = run(reaction(app, path, **({'strength': 'medium'} if path.endswith('submit') else {})))
    assert response.status_code == 502 and not state['increments']
    assert len(state['writes']) == 1 and state['writes'][0][0] == 'RPC'


@pytest.mark.parametrize('path', ['view', 'resonance', 'resonances/submit', 'resonances/delete'])
def test_request_cannot_redirect_row_metrics_to_another_question(reaction_app, path):
    app, state = reaction_app
    values = {'q_key': 'forged:unrelated'}
    if path.endswith('submit'):
        values['strength'] = 'medium'
    response = run(reaction(app, path, **values))
    assert response.status_code == 400
    assert not state['writes'] and not state['increments']


@pytest.mark.parametrize('iid', ['reflection:db-id', 'reflection:public-id'])
@pytest.mark.parametrize('requested', [None, 'generated:canonical'])
def test_canonical_saved_row_key_and_old_public_aliases_survive(reaction_app, iid, requested):
    app, state = reaction_app
    context = run(api._resolve_qna_context_for_reaction(viewer_user_id='viewer',
                  q_instance_id=iid, q_key=requested))
    assert context['q_key'] == 'generated:canonical'
    assert context['target_user_id'] == 'owner'
    assert context['q_instance_id'] == 'reflection:public-id'


@pytest.mark.parametrize('change,expected', [('denied', 404), ('unfollowed', 403), ('self', 400)])
def test_current_owner_and_follow_permissions_still_block_writes(reaction_app, change, expected):
    app, state = reaction_app
    if change == 'self':
        state['viewer'] = 'owner'
    else:
        state[change] = True
    response = run(reaction(app, 'resonance'))
    assert response.status_code == expected
    assert not state['writes'] and not state['increments']
