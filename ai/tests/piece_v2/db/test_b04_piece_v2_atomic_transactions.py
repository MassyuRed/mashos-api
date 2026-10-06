"""B4 disabled terminal owner: synthetic native transactions + pure adapter tests.

Concurrency requires committed fixtures visible to independent connections.
Each native test creates its own uniquely named database in the SAME explicitly
acknowledged local test server, and drops only that generated database afterwards.
The existing B2 URL boundary and synthetic generators remain unchanged. No live
credentials, remote host, migration history, production data, skip or fake DB.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import runpy
import sys
from threading import Barrier
import time
from uuid import uuid4

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / 'ai/services/ai_inference'))
from piece_v2_contract import PieceContractError
from piece_v2_quota import project_piece_quota
from piece_v2_store import save_piece, set_piece_visibility, delete_piece

_B2 = runpy.run_path(str(Path(__file__).with_name('test_b02_piece_v2_foundation.py')))
_M3 = _ROOT / 'supabase/migrations/20260808_003_piece_v2_rls_and_staging.sql'
_M4 = _ROOT / 'supabase/migrations/20260808_004_piece_v2_atomic_functions.sql'
_OWNER, _VIEWER = _B2['_OWNER'], _B2['_VIEWER']
_SAVE_FIELDS = ('p_owner_user_id','p_preview_id','p_expected_preview_revision',
                'p_piece_text_hash','p_content_payload_hash','p_visual_recipe_hash',
                'p_idempotency_key_hash','p_visibility_scope')


@pytest.fixture
def database():
    boundary = runpy.run_path(str(Path(__file__).with_name('conftest.py')))
    url = boundary['validate_disposable_database_url'](
        os.environ.get('PIECE_V2_TEST_DATABASE_URL',''),
        os.environ.get('PIECE_V2_TEST_DATABASE_DISPOSABLE_ACK',''))
    import psycopg as pg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo
    name = 'piece_v2_test_b4_' + uuid4().hex
    roles_created, created, conn = [], False, None
    with pg.connect(url, autocommit=True, connect_timeout=3) as admin:
        assert admin.info.dbname.startswith('piece_v2_test')
        assert admin.execute('SELECT rolsuper FROM pg_roles WHERE rolname=current_user').fetchone() == (True,)
        assert admin.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f','S')").fetchone() == (0,)
        try:
            for role in _B2['_ROLES']:
                if not admin.execute('SELECT 1 FROM pg_roles WHERE rolname=%s',(role,)).fetchone():
                    admin.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOBYPASSRLS').format(sql.Identifier(role)))
                    roles_created.append(role)
            admin.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(sql.Identifier(name)))
            created = True
            child_url = make_conninfo(url, dbname=name)
            conn = pg.connect(child_url, autocommit=True, connect_timeout=3)
            conn.execute("SET statement_timeout='8s'")
            conn.execute('CREATE TABLE public.mymodel_reflections (' + ','.join(_B2['_LEGACY_COLUMNS']) + ')')
            columns = ','.join(c.split()[0] for c in _B2['_LEGACY_COLUMNS'])
            conn.execute('CREATE VIEW public.pieces WITH (security_invoker=true) AS SELECT ' + columns + ' FROM public.mymodel_reflections')
            conn.execute('REVOKE ALL ON public.pieces FROM PUBLIC,anon,authenticated')
            conn.execute('GRANT SELECT ON public.pieces TO service_role')
            conn.execute(_B2['_M1'].read_text())
            conn.execute(_B2['_M2'].read_text())
            conn.execute(_M3.read_text())
            conn.execute('CREATE TABLE public.profiles (id uuid PRIMARY KEY, subscription_tier text)')
            conn.execute('INSERT INTO public.profiles VALUES (%s,%s)', (_OWNER,'free'))
            conn.execute(_M4.read_text())
            yield conn, pg, child_url
        finally:
            if conn is not None:
                conn.close()
            if created:
                admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
                assert admin.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone() is None
            for role in reversed(roles_created):
                admin.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
            assert admin.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f','S')").fetchone() == (0,)


def _preview(conn):
    row = _B2['_record'](fmt='short_essay')
    row['expires_at'] = conn.execute("SELECT clock_timestamp()+interval '10 minutes'").fetchone()[0]
    _B2['_insert'](conn, 'piece_records', row)
    return row


def _args(row, *, key='synthetic-save', visibility='private', owner=_OWNER):
    return dict(zip(_SAVE_FIELDS, (owner,row['id'],1,row['piece_text_hash'],
        row['content_payload_hash'],row['visual_recipe_hash'],hashlib.sha256(key.encode()).hexdigest(),visibility)))


def _rpc(conn, name, args, *, role='service_role'):
    from psycopg import sql
    with conn.transaction():
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role)))
        query = sql.SQL('SELECT public.{}({})').format(sql.Identifier(name), sql.SQL(',').join(
            sql.SQL('{} => {}').format(sql.Identifier(k),sql.Placeholder()) for k in args))
        return conn.execute(query, list(args.values())).fetchone()[0]


def _save(conn, row, **kwargs):
    return _rpc(conn, 'piece_save_v2', _args(row, **kwargs))


def _used(conn):
    return conn.execute('SELECT count(*) FROM public.piece_quota_consumptions').fetchone()[0]


def _seed_usage(conn, count):
    for _ in range(count):
        conn.execute("WITH stamp AS (SELECT clock_timestamp() AS t) INSERT INTO public.piece_quota_consumptions(owner_user_id,piece_id,month_key,subscription_tier_at_consumption,consumed_at,save_idempotency_key_hash) SELECT %s,%s,to_char(t AT TIME ZONE 'Asia/Tokyo','YYYY-MM'),'free',t,%s FROM stamp",
                     (_OWNER,uuid4(),uuid4().hex*2))


def _parallel(pg, url, calls):
    barrier = Barrier(len(calls))
    def worker(call):
        with pg.connect(url,autocommit=True,connect_timeout=3) as c:
            c.execute("SET statement_timeout='8s'")
            barrier.wait(timeout=5)
            try:
                return _rpc(c,*call)
            except pg.Error as exc:
                return exc.diag.message_primary
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [pool.submit(worker,call) for call in calls]
        return [f.result(timeout=12) for f in futures]


def test_b04_native_privileges_and_no_legacy_cutover(database):
    conn, pg, _ = database
    before = _B2['_legacy_identity'](conn)
    with pytest.raises(pg.errors.RaiseException,match='PIECE_B4_TARGET_EXISTS'):
        conn.execute(_M4.read_text())
    functions = conn.execute("SELECT oid::regprocedure::text,prosecdef,proconfig FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname IN ('piece_save_v2','piece_set_visibility_v2','piece_delete_v2')").fetchall()
    assert len(functions)==3
    for signature,definer,settings in functions:
        assert definer and settings==['search_path=pg_catalog']
        for role in _B2['_ROLES']:
            assert conn.execute('SELECT has_function_privilege(%s,%s,%s)',(role,signature,'EXECUTE')).fetchone()==(role=='service_role',)
    row = _preview(conn)
    for role in ('anon','authenticated'):
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _rpc(conn,'piece_save_v2',_args(row),role=role)
    for table in _B2['_TABLES']:
        for role in _B2['_ROLES']:
            for permission in ('INSERT','UPDATE','DELETE','TRUNCATE'):
                assert conn.execute('SELECT has_table_privilege(%s,%s,%s)',(role,'public.'+table,permission)).fetchone()==(False,)
    assert _B2['_legacy_identity'](conn)==before
    assert _used(conn)==0


@pytest.mark.parametrize('visibility', [None,'private','public'])
def test_b04_native_first_save_replay_preserves_content(database,visibility):
    conn, _, _ = database
    row = _preview(conn)
    assert _used(conn)==0
    first = _save(conn,row,visibility=visibility)
    second = _save(conn,row,visibility=visibility)
    assert first['piece_id']==second['piece_id']==str(row['id'])
    assert first['consumption_id']==second['consumption_id']
    assert not first['idempotency_replayed'] and second['idempotency_replayed']
    assert first['visibility_scope']==(visibility or 'private')
    assert _used(conn)==1
    saved = conn.execute('SELECT to_jsonb(r) FROM public.piece_records r WHERE id=%s',(row['id'],)).fetchone()[0]
    for key in ('piece_text','piece_text_hash','content_payload','content_payload_hash','format_type','visual_recipe','visual_recipe_hash','source_lineage'):
        assert saved[key]==row[key]
    assert saved['lifecycle_status']=='saved' and saved['expires_at'] is None and saved['row_version']==2
    assert conn.execute("SELECT month_key=to_char(consumed_at AT TIME ZONE 'Asia/Tokyo','YYYY-MM'),consumed_at=saved_at FROM public.piece_quota_consumptions q JOIN public.piece_records r ON r.id=q.piece_id").fetchone()==(True,True)
    for table in ('piece_record_metrics','piece_record_reads','piece_record_resonances'):
        assert conn.execute('SELECT count(*) FROM public.'+table).fetchone()==(0,)


@pytest.mark.parametrize('field,value,code', [
    ('p_owner_user_id',None,'PIECE_AUTH_REQUIRED'),
    ('p_owner_user_id',_VIEWER,'PIECE_NOT_FOUND'),
    ('p_preview_id',uuid4(),'PIECE_NOT_FOUND'),
    ('p_expected_preview_revision',2,'PIECE_PREVIEW_STALE'),
    ('p_expected_preview_revision',0,'PIECE_REQUEST_INVALID'),
    ('p_expected_preview_revision',None,'PIECE_REQUEST_INVALID'),
    ('p_piece_text_hash','0'*64,'PIECE_HASH_MISMATCH'),
    ('p_content_payload_hash','0'*64,'PIECE_HASH_MISMATCH'),
    ('p_visual_recipe_hash','0'*64,'PIECE_HASH_MISMATCH'),
    ('p_idempotency_key_hash',None,'PIECE_REQUEST_INVALID'),
    ('p_visibility_scope','unknown','PIECE_REQUEST_INVALID'),
])
def test_b04_native_invalid_save_has_no_effect(database,field,value,code):
    conn, pg, _ = database
    row = _preview(conn); args = _args(row); args[field]=value
    with pytest.raises(pg.errors.RaiseException,match='(?m)^'+code+'$'):
        _rpc(conn,'piece_save_v2',args)
    assert _used(conn)==0
    assert conn.execute('SELECT lifecycle_status FROM public.piece_records').fetchone()==('preview_draft',)
    assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone()==(0,)


@pytest.mark.parametrize('state', ['cancelled','rejected','expired'])
def test_b04_native_terminal_preview_cannot_save(database,state):
    conn,pg,_=database; row=_preview(conn)
    conn.execute('UPDATE public.piece_records SET lifecycle_status=%s WHERE id=%s',(state,row['id']))
    with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_CONFLICT$'): _save(conn,row)
    assert _used(conn)==0


@pytest.mark.parametrize('tier,limit', [('free',5),('plus',30),('unknown',5)])
def test_b04_native_current_tier_limit_and_downgrade(database,tier,limit):
    conn,pg,_=database; row=_preview(conn)
    _seed_usage(conn,limit)
    conn.execute('UPDATE public.profiles SET subscription_tier=%s',(tier,))
    with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_QUOTA_EXHAUSTED$'): _save(conn,row)
    assert _used(conn)==limit
    conn.execute("UPDATE public.profiles SET subscription_tier='premium'")
    result=_save(conn,row)
    assert result['piece_id']==str(row['id']) and _used(conn)==limit+1
    assert conn.execute('SELECT subscription_tier_at_consumption FROM public.piece_quota_consumptions WHERE piece_id=%s',(row['id'],)).fetchone()==('premium',)
    conn.execute("UPDATE public.profiles SET subscription_tier='free'")
    # Downgrade does not invalidate successful replay or alter the saved artifact.
    assert _save(conn,row)['consumption_id']==result['consumption_id']
    with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_QUOTA_EXHAUSTED$'):
        _save(conn,_preview(conn),key='new-after-downgrade')


@pytest.mark.parametrize('tier,limit', [('free',5),('plus',30)])
def test_b04_native_concurrent_remaining_one(database,tier,limit):
    conn,pg,url=database
    conn.execute('UPDATE public.profiles SET subscription_tier=%s',(tier,)); _seed_usage(conn,limit-1)
    a,b=_preview(conn),_preview(conn)
    results=_parallel(pg,url,[('piece_save_v2',_args(a,key='a')),('piece_save_v2',_args(b,key='b'))])
    assert sum(isinstance(r,dict) for r in results)==1
    assert results.count('PIECE_QUOTA_EXHAUSTED')==1
    assert _used(conn)==limit
    assert conn.execute("SELECT count(*) FROM public.piece_records WHERE lifecycle_status='saved'").fetchone()==(1,)


@pytest.mark.parametrize('same_preview,same_key', [(True,True),(True,False),(False,True),(False,False)])
def test_b04_native_concurrent_idempotency(database,same_preview,same_key):
    conn,pg,url=database; a=_preview(conn); b=a if same_preview else _preview(conn)
    results=_parallel(pg,url,[('piece_save_v2',_args(a,key='a')),('piece_save_v2',_args(b,key='a' if same_key else 'b'))])
    successes=[r for r in results if isinstance(r,dict)]
    if same_preview and same_key:
        assert len(successes)==2 and _used(conn)==1
        assert successes[0]['consumption_id']==successes[1]['consumption_id']
        assert sorted(r['idempotency_replayed'] for r in successes)==[False,True]
    elif same_preview or same_key:
        assert len(successes)==1 and results.count('PIECE_CONFLICT')==1 and _used(conn)==1
    else:
        assert len(successes)==2 and _used(conn)==2


def test_b04_native_injected_ledger_failure_rolls_back_save(database):
    conn,pg,_=database; row=_preview(conn)
    conn.execute("CREATE FUNCTION public.synthetic_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_LEDGER_FAILURE'; END $$")
    conn.execute('CREATE TRIGGER synthetic_fail BEFORE INSERT ON public.piece_quota_consumptions FOR EACH ROW EXECUTE FUNCTION public.synthetic_fail()')
    with pytest.raises(pg.errors.RaiseException,match='SYNTHETIC_LEDGER_FAILURE'): _save(conn,row)
    assert _used(conn)==0
    assert conn.execute('SELECT lifecycle_status,saved_at,save_idempotency_key_hash,row_version FROM public.piece_records').fetchone()==('preview_draft',None,None,1)
    assert conn.execute('SELECT count(*) FROM public.piece_quota_month_locks').fetchone()==(0,)


def test_b04_native_visibility_version_and_replay_do_not_consume(database):
    conn,pg,_=database; row=_preview(conn); first=_save(conn,row)
    args=dict(p_owner_user_id=_OWNER,p_piece_id=row['id'],p_expected_row_version=2,p_visibility_scope='public')
    assert _rpc(conn,'piece_set_visibility_v2',args)['row_version']==3
    with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_CONFLICT$'):
        _rpc(conn,'piece_set_visibility_v2',dict(args,p_visibility_scope='private'))
    replay=_save(conn,row)
    assert replay['visibility_scope']=='public' and replay['row_version']==3
    assert replay['consumption_id']==first['consumption_id'] and _used(conn)==1
    args.update(p_expected_row_version=3,p_visibility_scope='private')
    assert _rpc(conn,'piece_set_visibility_v2',args)['row_version']==4
    assert conn.execute('SELECT count(*) FROM public.pieces_v2_staging').fetchone()==(0,)
    assert _used(conn)==1


def _delete_args(row,key='synthetic-delete',version=2):
    return dict(p_owner_user_id=_OWNER,p_piece_id=row['id'],p_expected_row_version=version,
                p_idempotency_key_hash=hashlib.sha256(key.encode()).hexdigest())


def test_b04_native_delete_purges_children_preserves_quota_and_receipts(database):
    conn,pg,url=database; row=_preview(conn); first=_save(conn,row)
    _B2['_insert'](conn,'piece_record_metrics',dict(piece_id=row['id']))
    _B2['_insert'](conn,'piece_record_reads',dict(piece_id=row['id'],viewer_user_id=_VIEWER))
    _B2['_insert'](conn,'piece_record_resonances',dict(piece_id=row['id'],owner_user_id=_OWNER,viewer_user_id=_VIEWER))
    _B2['_insert'](conn,'piece_export_receipts',dict(owner_user_id=_OWNER,piece_id=row['id'],
        idempotency_key_hash='f'*64,piece_text_hash=row['piece_text_hash'],visual_recipe_hash=row['visual_recipe_hash'],outcome='succeeded'))
    results=_parallel(pg,url,[('piece_delete_v2',_delete_args(row)),('piece_delete_v2',_delete_args(row))])
    assert all(isinstance(r,dict) for r in results)
    assert results[0]['receipt_id']==results[1]['receipt_id']
    assert sorted(r['idempotency_replayed'] for r in results)==[False,True]
    for table in ('piece_records','piece_record_metrics','piece_record_reads','piece_record_resonances'):
        assert conn.execute('SELECT count(*) FROM public.'+table).fetchone()==(0,)
    assert _used(conn)==1
    assert conn.execute('SELECT consumption_id::text FROM public.piece_quota_consumptions').fetchone()==(first['consumption_id'],)
    for table in ('piece_export_receipts','piece_delete_receipts'):
        assert conn.execute('SELECT count(*) FROM public.'+table).fetchone()==(1,)
    with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_NOT_FOUND$'): _save(conn,row)
    with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_CONFLICT$'):
        _save(conn,_preview(conn))  # Deleted Piece's save key remains consumed.
    assert _used(conn)==1


def test_b04_native_delete_rejects_other_owner_stale_and_rolls_back_failure(database):
    conn,pg,_=database; row=_preview(conn); _save(conn,row)
    for args,code in [(dict(_delete_args(row),p_owner_user_id=_VIEWER),'PIECE_NOT_FOUND'),
                      (_delete_args(row,version=1),'PIECE_CONFLICT')]:
        with pytest.raises(pg.errors.RaiseException,match='(?m)^'+code+'$'):
            _rpc(conn,'piece_delete_v2',args)
    conn.execute("CREATE FUNCTION public.synthetic_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_DELETE_FAILURE'; END $$")
    conn.execute('CREATE TRIGGER synthetic_fail BEFORE DELETE ON public.piece_records FOR EACH ROW EXECUTE FUNCTION public.synthetic_fail()')
    with pytest.raises(pg.errors.RaiseException,match='SYNTHETIC_DELETE_FAILURE'):
        _rpc(conn,'piece_delete_v2',_delete_args(row))
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone()==(1,)
    assert conn.execute('SELECT count(*) FROM public.piece_delete_receipts').fetchone()==(0,)
    assert _used(conn)==1


def test_b04_native_preview_expiring_during_month_lock_wait(database):
    conn,pg,url=database; row=_preview(conn)
    month=conn.execute("SELECT to_char(clock_timestamp() AT TIME ZONE 'Asia/Tokyo','YYYY-MM')").fetchone()[0]
    conn.execute('INSERT INTO public.piece_quota_month_locks(owner_user_id,month_key) VALUES(%s,%s)',(_OWNER,month))
    with pg.connect(url,autocommit=False) as holder, pg.connect(url,autocommit=True) as worker:
        holder.execute('SELECT * FROM public.piece_quota_month_locks FOR UPDATE')
        worker.execute("SET statement_timeout='8s'")
        conn.execute("UPDATE public.piece_records SET expires_at=clock_timestamp()+interval '1 second' WHERE id=%s",(row['id'],))
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(_rpc,worker,'piece_save_v2',_args(row))
            try:
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    if conn.execute('SELECT cardinality(pg_blocking_pids(%s))',(worker.info.backend_pid,)).fetchone()[0]: break
                    time.sleep(0.01)
                else: pytest.fail('SAVE_DID_NOT_WAIT_ON_MONTH_LOCK')
                conn.execute("SELECT pg_sleep(greatest(0,extract(epoch from (expires_at-clock_timestamp())))+0.05) FROM public.piece_records WHERE id=%s",(row['id'],))
            finally:
                holder.commit()
            with pytest.raises(pg.errors.RaiseException,match='(?m)^PIECE_PREVIEW_EXPIRED$'):
                future.result(timeout=8)
    assert _used(conn)==0
    assert conn.execute('SELECT lifecycle_status FROM public.piece_records').fetchone()==('preview_draft',)


@pytest.mark.parametrize('tier,count,limit,remaining,can_save', [
    ('free',0,5,5,True),('free',5,5,0,False),('free',6,5,0,False),
    ('plus',29,30,1,True),('plus',30,30,0,False),('premium',100,None,None,True),
    ('unknown',5,5,0,False),
])
def test_b04_quota_projection(tier,count,limit,remaining,can_save):
    value=project_piece_quota(server_tier=tier,saved_count=count,
                             server_now=datetime(2026,9,30,15,tzinfo=timezone.utc))
    assert value['month_key']=='2026-10'
    assert (value['save_limit'],value['remaining_count'],value['can_save'])==(limit,remaining,can_save)
    assert set(value)=={'contract_version','subscription_tier','month_key','save_limit','saved_count','remaining_count','can_save'}
    before=project_piece_quota(server_tier=tier,saved_count=count,
        server_now=datetime(2026,9,30,14,59,59,tzinfo=timezone.utc))
    assert before['month_key']=='2026-09'


def _request_for(row):
    return dict(preview_id=str(row['id']),expected_preview_revision=1,
                piece_text_hash=row['piece_text_hash'],content_payload_hash=row['content_payload_hash'],
                visual_recipe_hash=row['visual_recipe_hash'])


@pytest.mark.parametrize('key,value', [('owner_user_id',str(_VIEWER)),('subscription_tier','premium'),
    ('save_limit',999),('piece_text','SYNTHETIC_FORBIDDEN_BODY'),('raw_input','SYNTHETIC_RAW'),
    ('expected_preview_revision',True),('visibility_scope','unknown')])
def test_b04_store_rejects_client_authority_and_body(key,value):
    row=_B2['_record'](); request=_request_for(row); request[key]=value; calls=[]
    async def rpc(*args): calls.append(args); raise AssertionError('must not call')
    with pytest.raises(PieceContractError,match='PIECE_REQUEST_INVALID'):
        asyncio.run(save_piece(authenticated_user_id=str(_OWNER),request=request,idempotency_key='test',rpc=rpc))
    assert calls==[]


def test_b04_store_native_one_rpc_and_stable_errors(database):
    conn,pg,_=database; row=_preview(conn); calls=[]
    async def rpc(name,args):
        calls.append(name)
        try: return _rpc(conn,name,args)
        except pg.Error as exc: raise PieceContractError(exc.diag.message_primary) from None
    first=asyncio.run(save_piece(authenticated_user_id=str(_OWNER),request=_request_for(row),idempotency_key='test',rpc=rpc))
    assert calls==['piece_save_v2'] and not first['idempotency_replayed']
    visibility=asyncio.run(set_piece_visibility(authenticated_user_id=str(_OWNER),piece_id=str(row['id']),
        request=dict(expected_row_version=2,visibility_scope='public'),rpc=rpc))
    assert visibility['row_version']==3
    deleted=asyncio.run(delete_piece(authenticated_user_id=str(_OWNER),piece_id=str(row['id']),
        request=dict(expected_row_version=3),idempotency_key='delete',rpc=rpc))
    assert deleted['outcome']=='succeeded' and _used(conn)==1
    assert calls==['piece_save_v2','piece_set_visibility_v2','piece_delete_v2']
    with pytest.raises(PieceContractError,match='(?m)^PIECE_NOT_FOUND$'):
        asyncio.run(save_piece(authenticated_user_id=str(_OWNER),request=_request_for(row),idempotency_key='test',rpc=rpc))


def test_b04_store_masks_provider_body_and_rejects_open_response():
    row=_B2['_record']()
    async def broken(*args): raise RuntimeError('SYNTHETIC_PRIVATE_PROVIDER_BODY')
    async def open_body(*args): return {'piece_text':'SYNTHETIC_PRIVATE_PROVIDER_BODY'}
    for rpc in (broken,open_body):
        with pytest.raises(PieceContractError) as exc:
            asyncio.run(save_piece(authenticated_user_id=str(_OWNER),request=_request_for(row),idempotency_key='test',rpc=rpc))
        assert str(exc.value)=='PIECE_TEMPORARILY_UNAVAILABLE'
