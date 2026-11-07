"""Legacy public aliases on the existing disposable native PostgreSQL harness.

The unchanged B4 fixture validates loopback/socket + explicit disposable ACK,
empty parent database and superuser, then creates/drops a unique child database.
Only synthetic legacy rows/policies are added in that child. Two execution
connections have distinct PostgreSQL backend PIDs; a third connection holds a
test gate so overlap is observed before release. No live target or fake driver.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
import runpy
import time
from uuid import uuid4

import pytest


_B4 = runpy.run_path(str(Path(__file__).with_name('test_b04_piece_v2_atomic_transactions.py')))
database = _B4['database']
_ROOT = _B4['_ROOT']
_OWNER, _VIEWER = _B4['_OWNER'], _B4['_VIEWER']
_LEGACY_TABLES = ('mymodel_reflections', 'mymodel_qna_metrics',
                  'mymodel_qna_resonances', 'mymodel_qna_echoes')


@pytest.fixture
def legacy_database(database):
    conn, pg, url = database
    # B4 already created the protected 21-column legacy source and bridges.
    # Its definition is reused unchanged rather than recreated or widened.
    columns = dict(conn.execute("select column_name,udt_name from information_schema.columns "
        "where table_schema='public' and table_name='mymodel_reflections'").fetchall())
    assert {key: columns[key] for key in ('id','public_id','owner_user_id','q_key','question',
            'source_type','is_active','status')} == {
        'id':'uuid','public_id':'text','owner_user_id':'uuid','q_key':'text','question':'text',
        'source_type':'text','is_active':'bool','status':'text'}
    conn.execute('create schema auth')
    conn.execute('create table auth.users(id uuid primary key)')
    conn.execute('insert into auth.users values (%s),(%s)', (_OWNER, _VIEWER))
    conn.execute('''create table public.mymodel_qna_metrics(
        q_key text not null, views bigint not null default 0,
        resonances bigint not null default 0, updated_at timestamptz not null default now(),
        q_instance_id text);
        create unique index mymodel_qna_metrics_unique_global on public.mymodel_qna_metrics(q_key)
            where q_instance_id is null;
        create unique index mymodel_qna_metrics_unique_instance on public.mymodel_qna_metrics(q_instance_id)
            where q_instance_id is not null;
        create table public.mymodel_qna_resonances(
            viewer_user_id uuid not null references auth.users(id) on delete cascade,
            q_instance_id text not null, q_key text not null,
            created_at timestamptz not null default now(), primary key(viewer_user_id,q_instance_id));
        create table public.mymodel_qna_echoes(
            viewer_user_id uuid not null references auth.users(id) on delete cascade,
            q_instance_id text not null,
            target_user_id uuid not null references auth.users(id) on delete cascade,
            question_id integer not null, q_key text not null,
            strength text not null check(strength in ('small','medium','large')),
            created_at timestamptz not null default now(), id uuid default gen_random_uuid(), memo text,
            context_source_type text, context_question text, context_answer text,
            context_topic_key text, context_category text,
            primary key(viewer_user_id,q_instance_id), check(viewer_user_id<>target_user_id));''')
    # The B4 cluster role is NOBYPASSRLS. Model the actual service role's
    # existing legacy CRUD access with child-only RLS policies, without changing
    # cluster role attributes or the protected V2/bridge permissions.
    from psycopg import sql
    for table in _LEGACY_TABLES:
        conn.execute(sql.SQL('alter table public.{} enable row level security').format(sql.Identifier(table)))
        conn.execute(sql.SQL('create policy synthetic_service_only on public.{} '
            'for all to service_role using (true) with check (true)').format(sql.Identifier(table)))
        conn.execute(sql.SQL('grant select,insert,update,delete on public.{} to service_role').format(sql.Identifier(table)))
    conn.execute('grant usage on schema public,auth to service_role')
    for suffix in ('piece_legacy_metrics_atomic.sql', 'piece_legacy_reaction_alias.sql'):
        migrations = list((_ROOT / 'supabase/migrations').glob('*_' + suffix))
        assert len(migrations) == 1, 'Expected one canonical legacy migration per suffix'
        conn.execute(migrations[0].read_text())
    source_id = uuid4()
    public_id = 'synthetic-public-' + source_id.hex
    canonical = 'reflection:' + public_id
    key = 'generated:native:' + source_id.hex
    conn.execute('''insert into public.mymodel_reflections
        (id,public_id,owner_user_id,q_key,question,source_type,is_active,status)
        values (%s,%s,%s,%s,%s,'emotion_generated',true,'published')''',
        (source_id, public_id, _OWNER, key, '合成した公開用の問い'))
    yield dict(conn=conn, pg=pg, url=url, source=source_id, canonical=canonical, key=key,
               old='reflection:' + str(source_id), aliases=(canonical,public_id,str(source_id),
                                                          'reflection:' + str(source_id)))


def _args(case, operation, *, memo='合成したメモ'):
    from psycopg.types.json import Jsonb
    echo = (Jsonb(dict(strength='medium', memo=memo, question='合成した公開用の問い',
                      answer='合成した公開用の本文。', topic_key=None, category='生活'))
            if operation == 'echo' else None)
    return dict(p_source_id=case['source'], p_expected_owner=_OWNER, p_viewer_id=_VIEWER,
                p_canonical_id=case['canonical'], p_q_key=case['key'],
                p_operation=operation, p_echo=echo)


def _rpc(conn, case, operation):
    return _B4['_rpc'](conn, 'piece_apply_legacy_reaction', _args(case, operation))


def _seed_echo(case, iid):
    case['conn'].execute('''insert into public.mymodel_qna_echoes
        (viewer_user_id,q_instance_id,target_user_id,question_id,q_key,strength,memo)
        values (%s,%s,%s,0,%s,'small','変更前の合成メモ')''', (_VIEWER,iid,_OWNER,case['key']))


def _seed_reaction(case, iid):
    case['conn'].execute('''insert into public.mymodel_qna_resonances
        (viewer_user_id,q_instance_id,q_key) values (%s,%s,%s)''', (_VIEWER,iid,case['key']))
    _B4['_rpc'](case['conn'], 'piece_increment_legacy_metric',
               dict(p_q_key=case['key'],p_q_instance_id=iid,p_field='resonances',p_delta=1))


def _wait_blocked(monitor, pid, blocker, deadline):
    while time.monotonic() < deadline:
        blocking = monitor.execute('select pg_blocking_pids(%s)', (pid,)).fetchone()[0]
        if blocker in blocking:
            return
        time.sleep(0.01)
    pytest.fail('SYNTHETIC_TRANSACTION_DID_NOT_REACH_EXPECTED_LOCK')


@contextmanager
def _connections(case):
    pg, url = case['pg'], case['url']
    with pg.connect(url,autocommit=False,connect_timeout=3) as gate, \
            pg.connect(url,autocommit=True,connect_timeout=3) as first, \
            pg.connect(url,autocommit=True,connect_timeout=3) as second:
        connections = (case['conn'],gate,first,second)
        pids = [connection.execute('select pg_backend_pid()').fetchone()[0]
                for connection in connections]
        assert pids == [connection.info.backend_pid for connection in connections]
        assert len(set(pids)) == 4, 'Independent native execution connections required'
        for connection in (gate,first,second):
            connection.execute("set statement_timeout='8s'")
        try:
            yield gate, first, second
        finally:
            gate.rollback()


def _overlap(case, operations):
    with _connections(case) as (gate, first, second):
        gate.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))",
                     ('piece-legacy-reaction:' + case['canonical'],))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_rpc, connection, case, operation)
                       for connection,operation in zip((first,second),operations,strict=True)]
            try:
                deadline = time.monotonic() + 5
                for worker in (first,second):
                    _wait_blocked(case['conn'],worker.info.backend_pid,gate.info.backend_pid,deadline)
                assert not any(future.done() for future in futures)
            finally:
                gate.commit()
            return [future.result(timeout=12) for future in futures]


def _state_and_counts(case):
    conn = case['conn']
    reaction_count = conn.execute('select count(*) from public.mymodel_qna_resonances '
        'where viewer_user_id=%s and q_instance_id=any(%s)', (_VIEWER,list(case['aliases']))).fetchone()[0]
    global_count = conn.execute('select coalesce(sum(resonances),0) from public.mymodel_qna_metrics '
        'where q_key=%s and q_instance_id is null', (case['key'],)).fetchone()[0]
    instance_count = conn.execute('select coalesce(sum(resonances),0) from public.mymodel_qna_metrics '
        'where q_key=%s and q_instance_id=any(%s)', (case['key'],list(case['aliases']))).fetchone()[0]
    return reaction_count,global_count,instance_count


@pytest.mark.parametrize('existing_old_alias', [False,True])
def test_native_alias_add_add_has_one_state_and_one_counter(legacy_database,existing_old_alias):
    case=legacy_database
    if existing_old_alias:
        _seed_reaction(case,case['old'])
        _seed_echo(case,case['old'])
    # Both API aliases reach the same verified source/canonical RPC identity.
    # The independent callers take the two active add operations.
    results=_overlap(case,('resonate','echo'))
    assert sum(result['changed_count'] for result in results)==(0 if existing_old_alias else 1)
    assert all(result['q_instance_id']==case['canonical'] and result['resonated'] for result in results)
    assert _state_and_counts(case)==(1,1,1)
    expected=case['old'] if existing_old_alias else case['canonical']
    for table in ('mymodel_qna_resonances','mymodel_qna_echoes'):
        assert case['conn'].execute('select q_instance_id from public.'+table).fetchall()==[(expected,)]


@pytest.mark.parametrize('existing_old_alias', [False,True])
def test_native_alias_add_remove_commits_consistent_state(legacy_database,existing_old_alias):
    case=legacy_database
    if existing_old_alias:
        _seed_reaction(case,case['old'])
        _seed_echo(case,case['old'])
    results=_overlap(case,('echo','remove'))
    assert all(isinstance(result,dict) for result in results)
    count,global_count,instance_count=_state_and_counts(case)
    assert count in (0,1) and count==global_count==instance_count
    assert case['conn'].execute('select count(*) from public.mymodel_qna_echoes').fetchone()==(count,)


def _snapshot(case):
    return {table:case['conn'].execute('select to_jsonb(r) from public.'+table+
        ' r order by q_instance_id nulls first').fetchall()
        for table in ('mymodel_qna_echoes','mymodel_qna_resonances','mymodel_qna_metrics')}


@pytest.mark.parametrize('operation', ['echo','remove'])
def test_native_counter_failure_rolls_back_every_legacy_write(legacy_database,operation):
    case=legacy_database
    _seed_echo(case,case['old'])
    if operation=='remove':
        _seed_reaction(case,case['old'])
    before=_snapshot(case)
    case['conn'].execute('''create function public.synthetic_metric_failure() returns trigger
        language plpgsql as $$ begin raise exception 'SYNTHETIC_METRIC_FAILURE'; end $$;
        create trigger synthetic_metric_failure before insert or update on public.mymodel_qna_metrics
        for each row execute function public.synthetic_metric_failure();''')
    with pytest.raises(case['pg'].errors.RaiseException,match='SYNTHETIC_METRIC_FAILURE'):
        _rpc(case['conn'],case,operation)
    assert _snapshot(case)==before


@pytest.mark.parametrize('mutation', ['update','delete'])
def test_native_source_change_waits_for_inflight_reaction(legacy_database,mutation):
    case=legacy_database
    case['conn'].execute('insert into public.mymodel_qna_metrics(q_key,q_instance_id) values (%s,null)',
                         (case['key'],))
    with _connections(case) as (gate, first, second):
        gate.execute('select * from public.mymodel_qna_metrics where q_key=%s and '
                     'q_instance_id is null for update',(case['key'],))
        def change_source():
            with second.transaction():
                second.execute('set local role service_role')
                statement=('update public.mymodel_reflections set is_active=false where id=%s returning id'
                           if mutation=='update' else 'delete from public.mymodel_reflections where id=%s returning id')
                return second.execute(statement,(case['source'],)).fetchone()
        with ThreadPoolExecutor(max_workers=2) as pool:
            reaction=pool.submit(_rpc,first,case,'resonate')
            try:
                deadline=time.monotonic()+5
                # The RPC has acquired FOR SHARE on the source before it waits
                # for the existing global counter row held by this test gate.
                _wait_blocked(case['conn'],first.info.backend_pid,gate.info.backend_pid,deadline)
                change=pool.submit(change_source)
                _wait_blocked(case['conn'],second.info.backend_pid,first.info.backend_pid,deadline)
                assert not reaction.done() and not change.done()
            finally:
                gate.commit()
            assert reaction.result(timeout=12)['changed_count']==1
            assert change.result(timeout=12)==(case['source'],)
    if mutation=='update':
        assert case['conn'].execute('select is_active from public.mymodel_reflections '
                                    'where id=%s',(case['source'],)).fetchone()==(False,)
    else:
        assert case['conn'].execute('select count(*) from public.mymodel_reflections').fetchone()==(0,)


def test_native_legacy_rpc_acl_and_rls_do_not_grant_public_execution(legacy_database):
    case=legacy_database
    conn,pg=case['conn'],case['pg']
    for table in _LEGACY_TABLES:
        assert conn.execute('select relrowsecurity from pg_class where oid=%s::regclass',
                             ('public.'+table,)).fetchone()==(True,)
    for signature in (
            'public.piece_increment_legacy_metric(text,text,text,integer)',
            'public.piece_apply_legacy_reaction(uuid,uuid,uuid,text,text,text,jsonb)'):
        assert conn.execute('select prosecdef,proconfig from pg_proc where oid=%s::regprocedure',
                             (signature,)).fetchone()==(False,['search_path=pg_catalog'])
        for role in ('anon','authenticated','service_role'):
            assert conn.execute('select has_function_privilege(%s,%s,%s)',
                (role,signature,'EXECUTE')).fetchone()==(role=='service_role',)
    for role in ('anon','authenticated'):
        assert conn.execute("select has_schema_privilege(%s,'public','USAGE')",(role,)).fetchone()==(True,)
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _B4['_rpc'](conn,'piece_apply_legacy_reaction',_args(case,'resonate'),role=role)
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _B4['_rpc'](conn,'piece_increment_legacy_metric',dict(p_q_key=case['key'],
                p_q_instance_id=case['canonical'],p_field='views',p_delta=1),role=role)
    assert _state_and_counts(case)==(0,0,0)
    for table in _B4['_B2']['_TABLES']:
        for role in _B4['_B2']['_ROLES']:
            for permission in ('INSERT','UPDATE','DELETE','TRUNCATE'):
                assert conn.execute('select has_table_privilege(%s,%s,%s)',
                    (role,'public.'+table,permission)).fetchone()==(False,)
