"""Verified-row legacy identity aliases through the real public service/store.

Only the Supabase transport/auth corpus is synthetic; all state reads, the
existing counter RPC and canonical read writes run on isolated PostgreSQL WASM.
No legacy data rewrite or alias reaction-mutation acceptance is implied.
"""
import json
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

import piece_public_read_service as service
import piece_public_read_store as store
from piece_generated_access import generated_public_id
from piece_generated_identity import generated_instance_aliases
from test_emlis_q2_application import run
from test_piece_public_metric_atomicity import sql_db, sql_rpc


@pytest.fixture
def alias_case(sql_db, monkeypatch):
    viewer, owner = str(uuid4()), str(uuid4())
    row = dict(id=str(uuid4()), public_id=str(uuid4()), owner_user_id=owner,
               source_type='emotion_generated', q_key='alias:' + str(uuid4()),
               question='保存済みの問い', published_at='2026-11-07T00:00:00Z')
    aliases = generated_instance_aliases(row)
    canonical = generated_public_id(row)
    groups = {canonical: set(aliases)}
    with sql_db.lock:
        sql_db.proc.stdin.write(json.dumps({'script': True, 'sql': '''
            create table if not exists public.mymodel_qna_reads(
                viewer_user_id uuid not null, q_instance_id text not null,
                viewed_at timestamptz not null default now(),
                primary key(viewer_user_id,q_instance_id));
            create table if not exists public.mymodel_qna_resonances(
                viewer_user_id uuid not null,q_instance_id text not null,
                q_key text not null,created_at timestamptz not null default now(),
                primary key(viewer_user_id,q_instance_id));
        '''}) + '\n')
        sql_db.proc.stdin.flush()
        assert 'code' not in json.loads(sql_db.proc.stdout.readline())
    for iid, views, resonances in zip(aliases, (6, 3, 2, 1), (3, 2, 1, 0), strict=True):
        sql_db.query('insert into public.mymodel_qna_metrics(q_key,q_instance_id,views,resonances) '
                     'values ($1,$2,$3,$4)', [row['q_key'], iid, views, resonances])
    sql_db.query('insert into public.mymodel_qna_metrics(q_key,q_instance_id,views,resonances) '
                 'values ($1,null,12,6)', [row['q_key']])
    sql_db.query('insert into public.mymodel_qna_reads(viewer_user_id,q_instance_id) values ($1,$2)',
                 [viewer, row['id']])
    sql_db.query('insert into public.mymodel_qna_resonances(viewer_user_id,q_instance_id,q_key) '
                 'values ($1,$2,$3)', [viewer, 'reflection:' + row['id'], row['q_key']])
    calls = []
    state = dict(viewer=viewer, failed=None)

    def table_name(path):
        return {
            '/rest/v1/' + store.METRICS_READ_TABLE: 'mymodel_qna_metrics',
            '/rest/v1/' + store.READS_READ_TABLE: 'mymodel_qna_reads',
            '/rest/v1/' + store.RESONANCES_TABLE: 'mymodel_qna_resonances',
        }[path]

    async def get(path, *, params):
        calls.append(('GET', path, dict(params)))
        if state['failed'] == 'http':
            return httpx.Response(500, json={})
        if state['failed'] == 'shape':
            return httpx.Response(200, json={'invalid': 'rows'})
        if state['failed'] == 'timeout':
            raise TimeoutError('synthetic read interrupted')
        value = params['q_instance_id']
        ids = json.loads('[' + value[4:-1] + ']') if value.startswith('in.(') else [value[3:]]
        marks = ','.join('$' + str(index + 1) for index in range(len(ids)))
        where, args = f'q_instance_id in ({marks})', list(ids)
        if 'viewer_user_id' in params:
            args.append(params['viewer_user_id'][3:])
            where += ' and viewer_user_id=$' + str(len(args))
        table = table_name(path)
        selection = ('q_instance_id,q_key,views::int,resonances::int' if table == 'mymodel_qna_metrics'
                     else 'q_instance_id,viewer_user_id')
        result = sql_db.query(f'select {selection} from public.{table} where {where} '
                             'limit ' + params['limit'], args)
        assert 'code' not in result, result
        return httpx.Response(200, json=result['rows'])

    async def post(path, *, json, prefer=None, **kwargs):
        calls.append(('POST', path, dict(json)))
        assert path == '/rest/v1/' + store.READS_TABLE
        assert json['viewer_user_id'] == viewer and json['q_instance_id'] == canonical
        result = sql_db.query('insert into public.mymodel_qna_reads(viewer_user_id,q_instance_id,viewed_at) '
            'values ($1,$2,$3) on conflict(viewer_user_id,q_instance_id) do update '
            'set viewed_at=excluded.viewed_at', [viewer, canonical, json['viewed_at']])
        assert 'code' not in result, result
        return httpx.Response(204)

    async def rpc(name, payload, **kwargs):
        assert name == 'piece_increment_legacy_metric'
        assert payload['p_q_instance_id'] == canonical
        calls.append(('RPC', name, dict(payload)))
        result = sql_rpc(sql_db, payload['p_q_key'], payload['p_q_instance_id'],
                         payload['p_field'], payload['p_delta'])
        assert 'code' not in result, result
        return httpx.Response(200, json=result['rows'][0]['value'])

    async def access(**kwargs):
        assert kwargs['q_instance_id'] in aliases
        assert kwargs['viewer_user_id'] == state['viewer']
        return row

    async def owner_rows(target, **kwargs):
        assert target == owner
        return [row]

    async def following(**kwargs):
        return {owner}

    async def profiles(ids):
        return {owner: {'display_name': '公開名'}}

    async def allowed(**kwargs):
        return True

    async def noop(**kwargs):
        return None

    monkeypatch.setattr(store, 'sb_get', get)
    monkeypatch.setattr(store, '_sb_post_shared', post)
    monkeypatch.setattr(store, '_sb_post_rpc_shared', rpc)
    monkeypatch.setattr(service, 'resolve_generated_reflection_access', access)
    monkeypatch.setattr(service, 'fetch_active_emotion_generated_reflections_for_owner', owner_rows)
    monkeypatch.setattr(service, 'fetch_followed_owner_ids', following)
    monkeypatch.setattr(service, 'fetch_profiles_by_ids', profiles)
    monkeypatch.setattr(service, 'has_myprofile_link', allowed)
    monkeypatch.setattr(service, 'get_public_generated_reflection_text', lambda row: '保存済み本文です。')
    for name in ('enqueue_ranking_board_refresh', 'enqueue_account_status_refresh',
                 'enqueue_global_summary_refresh'):
        monkeypatch.setattr(service, name, noop)
    return sql_db, row, aliases, canonical, groups, state, calls


@pytest.mark.parametrize('public,id_value,expected', [
    ('pub', 'db', ('reflection:pub', 'pub', 'reflection:db', 'db')),
    ('reflection:pub', 'db', ('reflection:pub', 'pub', 'reflection:db', 'db')),
    (None, 'db', ('reflection:db', 'db')),
    ('db', 'db', ('reflection:db', 'db')),
    ('', '', ()),
])
def test_aliases_are_row_derived_and_match_existing_canonical_owner(public, id_value, expected):
    row = {'id': id_value, 'public_id': public}
    assert generated_instance_aliases(row) == expected
    assert generated_public_id(row) == (expected[0] if expected else '')


def test_actual_store_sums_old_counters_and_recovers_old_read_and_reaction(alias_case):
    db, row, aliases, canonical, groups, state, calls = alias_case
    metrics = run(store.fetch_instance_metrics({canonical}, alias_groups=groups))
    assert metrics[canonical]['views'] == 12 and metrics[canonical]['resonances'] == 6
    assert run(store.fetch_reads(state['viewer'], {canonical}, alias_groups=groups)) == {canonical}
    assert run(store.fetch_resonated_instances(state['viewer'], {canonical}, alias_groups=groups)) == {canonical}
    assert run(store.is_resonated(state['viewer'], canonical, alias_groups=groups))
    for _, _, params in calls:
        assert set(json.loads('[' + params['q_instance_id'][4:-1] + ']')) == set(aliases)
        assert int(params['limit']) >= 1
    assert all(kind == 'GET' for kind, *_ in calls)


def test_callers_without_groups_keep_exact_instance_contract(alias_case):
    db, row, aliases, canonical, groups, state, calls = alias_case
    metrics = run(store.fetch_instance_metrics({canonical}))
    assert metrics[canonical]['views'] == 6 and metrics[canonical]['resonances'] == 3
    assert metrics[canonical]['q_key'] == row['q_key']
    assert run(store.fetch_reads(state['viewer'], {canonical})) == set()
    assert run(store.fetch_resonated_instances(state['viewer'], {canonical})) == set()
    assert not run(store.is_resonated(state['viewer'], canonical))
    assert all(kind == 'GET' for kind, *_ in calls)


def test_service_list_and_unread_use_one_canonical_card_and_old_state(alias_case):
    db, row, aliases, canonical, groups, state, calls = alias_case
    payload = run(service.build_nexus_reflections_payload(viewer_user_id=state['viewer'],
        target_user_id=None, sort='latest', limit=20, following_only=True))
    assert payload['total_items'] == 1
    card = payload['items'][0]
    assert card['q_instance_id'] == canonical
    assert card['metrics'] == {'views': 12, 'resonances': 6}
    assert card['viewer_state'] == dict(is_new=False, is_resonated=True, can_resonate=True)
    unread = run(service.build_qna_public_unread_payload(viewer_user_id=state['viewer'],
                                                       target_user_id=row['owner_user_id']))
    assert unread['total_items'] == 1 and unread['unread_count'] == 0 and not unread['has_unread']
    status = run(service.build_qna_public_unread_status_payload(viewer_user_id=state['viewer']))
    assert not status['following_has_unread'] and not status['has_unread']
    assert all(kind == 'GET' for kind, *_ in calls)


@pytest.mark.parametrize('alias_index', range(4))
def test_service_detail_aliases_reread_same_saved_state_without_mutation(alias_case, alias_index):
    db, row, aliases, canonical, groups, state, calls = alias_case
    requested = aliases[alias_index]
    # Public URL handlers require a reflection-prefixed value; internal source
    # lookup compatibility also retains raw DB/public aliases for saved state.
    result = run(service._build_public_piece_detail_response(viewer_user_id=state['viewer'],
        q_instance_id=requested, mark_viewed=False))
    assert result['q_instance_id'] == canonical
    assert result['views'] == 12 and result['resonances'] == 6
    assert not result['is_new'] and result['is_resonated']
    assert result['body'] == '保存済み本文です。'
    assert all(kind == 'GET' for kind, *_ in calls)


def test_old_alias_view_writes_only_canonical_and_retains_old_metrics(alias_case):
    db, row, aliases, canonical, groups, state, calls = alias_case
    legacy_before = db.query('select q_instance_id,views::int,resonances::int from '
        'public.mymodel_qna_metrics where q_key=$1 and q_instance_id<>$2 order by q_instance_id',
        [row['q_key'], canonical])
    for expected, requested in zip((13, 14), ('reflection:' + row['id'], canonical), strict=True):
        result = run(service.build_qna_public_detail_payload(viewer_user_id=state['viewer'],
            q_instance_id=requested, mark_viewed=True))
        assert result['q_instance_id'] == canonical and result['views'] == expected
        assert result['resonances'] == 6 and result['is_resonated']
    assert db.query('select q_instance_id,views::int,resonances::int from '
        'public.mymodel_qna_metrics where q_key=$1 and q_instance_id<>$2 order by q_instance_id',
        [row['q_key'], canonical]) == legacy_before
    assert db.query('select views::int,resonances::int from public.mymodel_qna_metrics '
        'where q_key=$1 and q_instance_id is null', [row['q_key']])['rows'] == [
            {'views': 14, 'resonances': 6}]
    assert all(payload['q_instance_id'] == canonical for kind, _, payload in calls if kind == 'POST')
    assert all(payload['p_q_instance_id'] == canonical for kind, _, payload in calls if kind == 'RPC')


@pytest.mark.parametrize('failed', ['http', 'shape', 'timeout'])
@pytest.mark.parametrize('kind', ['metrics', 'reads', 'resonated', 'single'])
def test_incomplete_alias_read_is_reported_without_inventing_zero(alias_case, failed, kind):
    db, row, aliases, canonical, groups, state, calls = alias_case
    state['failed'] = failed
    functions = {
        'metrics': lambda: store.fetch_instance_metrics({canonical}, alias_groups=groups),
        'reads': lambda: store.fetch_reads(state['viewer'], {canonical}, alias_groups=groups),
        'resonated': lambda: store.fetch_resonated_instances(state['viewer'], {canonical}, alias_groups=groups),
        'single': lambda: store.is_resonated(state['viewer'], canonical, alias_groups=groups),
    }
    with pytest.raises(HTTPException) as error:
        run(functions[kind]())
    assert error.value.status_code == 502
    assert all(action == 'GET' for action, *_ in calls)


@pytest.mark.parametrize('kind', ['metrics', 'reads', 'resonated'])
@pytest.mark.parametrize('failed_chunk', [None, 2])
def test_512_aliases_are_read_once_in_bounded_chunks_or_fail_whole(monkeypatch, kind, failed_chunk):
    rows = [dict(id='db-' + str(index), public_id='pub-' + str(index)) for index in range(128)]
    groups = {generated_public_id(row): set(generated_instance_aliases(row)) for row in rows}
    all_aliases = set().union(*groups.values())
    old_state = {row['id'] for row in rows}
    assert len(all_aliases) == 512
    calls = []

    async def get(path, *, params):
        ids = json.loads('[' + params['q_instance_id'][4:-1] + ']')
        assert ids == sorted(ids) and len(ids) <= 200
        assert params['limit'] == str(len(ids))
        calls.append(ids)
        if len(calls) == failed_chunk:
            return httpx.Response(500, json={})
        if kind == 'metrics':
            payload = [dict(q_instance_id=iid, q_key='kept-key', views=1, resonances=2) for iid in ids]
        else:
            assert params['viewer_user_id'] == 'eq.viewer'
            payload = [dict(q_instance_id=iid) for iid in ids if iid in old_state]
        return httpx.Response(200, json=payload[:200])  # Model a bounded PostgREST page.

    monkeypatch.setattr(store, 'sb_get', get)
    functions = {
        'metrics': lambda: store.fetch_instance_metrics(set(groups), alias_groups=groups),
        'reads': lambda: store.fetch_reads('viewer', set(groups), alias_groups=groups),
        'resonated': lambda: store.fetch_resonated_instances('viewer', set(groups), alias_groups=groups),
    }
    if failed_chunk:
        with pytest.raises(HTTPException) as error:
            run(functions[kind]())
        assert error.value.status_code == 502 and len(calls) == failed_chunk
        return
    result = run(functions[kind]())
    assert [len(ids) for ids in calls] == [200, 200, 112]
    flattened = [iid for ids in calls for iid in ids]
    assert len(flattened) == len(set(flattened)) == 512
    assert set(flattened) == all_aliases
    if kind == 'metrics':
        assert set(result) == set(groups)
        assert all(value['views'] == 4 and value['resonances'] == 8 for value in result.values())
    else:
        assert result == set(groups)
