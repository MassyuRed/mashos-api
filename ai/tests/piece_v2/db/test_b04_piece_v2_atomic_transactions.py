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
_ACCOUNT_WITHDRAWAL = _ROOT / 'supabase/migrations/20261128053404_piece_account_withdrawal.sql'
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


def _preview(conn, *, owner=_OWNER):
    row = _B2['_record'](fmt='short_essay')
    row['owner_user_id'] = owner
    row['source_lineage']['source_input']['source_owner_user_id'] = str(owner)
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


_PUBLIC_FEED = _ROOT / 'supabase/migrations/20261121095000_piece_v2_public_feed.sql'


def _publication_schema(conn):
    conn.execute('CREATE TABLE public.emotions (id uuid PRIMARY KEY, user_id uuid, is_secret boolean NOT NULL)')
    conn.execute('''CREATE TABLE public.myprofile_links (
        viewer_user_id uuid NOT NULL, owner_user_id uuid NOT NULL,
        PRIMARY KEY(viewer_user_id,owner_user_id))''')
    conn.execute(_PUBLIC_FEED.read_text())


def _publication_save(conn, *, source_owner=_OWNER, secret=False, include_source=True, key='publish-piece'):
    source_id = uuid4()
    row = _B2['_record'](fmt='short_essay')
    row['expires_at'] = conn.execute("SELECT clock_timestamp()+interval '10 minutes'").fetchone()[0]
    row['source_input_id'] = str(source_id)
    row['source_lineage']['source_input']['source_input_id'] = str(source_id)
    if include_source:
        conn.execute('INSERT INTO public.emotions VALUES (%s,%s,%s)', (source_id, source_owner, secret))
    _B2['_insert'](conn, 'piece_records', row)
    saved = _save(conn, row, key=key)
    return source_id, row, saved


def _read_public_feed(conn, viewer, *, target=None, follows_only=False, order='latest', limit=20,
                      role='service_role'):
    return _rpc(conn, 'piece_read_public_feed_v2', dict(p_viewer_user_id=viewer,
        p_target_owner_user_id=target, p_following_only=follows_only, p_sort=order, p_limit=limit), role=role)


def test_public_feed_uses_current_direction_and_visibility_without_consuming_quota(database):
    conn, pg, _ = database
    _publication_schema(conn)
    source_id, row, saved = _publication_save(conn)
    owner_params = dict(p_owner_user_id=_OWNER, p_piece_id=row['id'],
                        p_expected_row_version=saved['row_version'], p_visibility_scope='public')
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_OWNER, _VIEWER))
    assert _read_public_feed(conn, _OWNER) == []
    assert _read_public_feed(conn, _VIEWER, target=_OWNER) == []
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_NOT_FOUND$'):
        _rpc(conn, 'piece_set_visibility_v2', dict(owner_params, p_owner_user_id=_VIEWER))

    published = _rpc(conn, 'piece_set_visibility_v2', owner_params)
    owner_feed = _read_public_feed(conn, _OWNER)
    assert len(owner_feed) == 1
    assert set(owner_feed[0]) == {'public_id', 'owner_user_id', 'body', 'published_at'}
    assert owner_feed[0]['public_id'] == 'piece:' + str(row['id'])
    assert owner_feed[0]['owner_user_id'] == str(_OWNER)
    assert owner_feed[0]['body'] == row['piece_text']
    assert _read_public_feed(conn, _OWNER, follows_only=True) == []
    assert _read_public_feed(conn, _OWNER, target=_OWNER, follows_only=True) == owner_feed
    assert _read_public_feed(conn, _VIEWER) == []
    assert _read_public_feed(conn, _VIEWER, target=_OWNER) == []
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_VIEWER, _OWNER))
    assert _read_public_feed(conn, _VIEWER, follows_only=True) == owner_feed

    for role in ('anon', 'authenticated'):
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _read_public_feed(conn, _OWNER, role=role)
        with pytest.raises(pg.errors.InsufficientPrivilege):
            _rpc(conn, 'piece_set_visibility_v2', owner_params, role=role)

    conn.execute('DELETE FROM public.myprofile_links WHERE viewer_user_id = %s', (_VIEWER,))
    assert _read_public_feed(conn, _VIEWER, target=_OWNER) == []
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_VIEWER, _OWNER))
    conn.execute('UPDATE public.emotions SET is_secret=true WHERE id=%s', (source_id,))
    assert _read_public_feed(conn, _VIEWER, target=_OWNER) == []
    assert _read_public_feed(conn, _OWNER) == []
    withdrawn = _rpc(conn, 'piece_set_visibility_v2',
        dict(owner_params, p_expected_row_version=published['row_version'], p_visibility_scope='private'))
    assert withdrawn['visibility_scope'] == 'private'
    conn.execute('UPDATE public.emotions SET is_secret=false WHERE id=%s', (source_id,))
    assert _read_public_feed(conn, _VIEWER, target=_OWNER) == []
    assert conn.execute('SELECT piece_text FROM public.piece_records WHERE id=%s', (row['id'],)).fetchone()[0] == row['piece_text']
    assert _used(conn) == 1


@pytest.mark.parametrize('source_owner,secret,include_source', [
    (_OWNER, True, True), (_VIEWER, False, True), (_OWNER, False, False),
])
def test_publication_rejects_secret_other_owner_or_missing_original(database, source_owner, secret, include_source):
    conn, pg, _ = database
    _publication_schema(conn)
    _, row, saved = _publication_save(conn, source_owner=source_owner, secret=secret, include_source=include_source)
    with pytest.raises(pg.errors.RaiseException, match='(?m)^PIECE_PUBLICATION_NOT_ALLOWED$'):
        _rpc(conn, 'piece_set_visibility_v2', dict(p_owner_user_id=_OWNER, p_piece_id=row['id'],
            p_expected_row_version=saved['row_version'], p_visibility_scope='public'))
    assert conn.execute('SELECT visibility_scope,row_version FROM public.piece_records WHERE id=%s',
                        (row['id'],)).fetchone() == ('private', saved['row_version'])


def test_publication_feed_orders_and_limits_the_published_rows(database):
    conn, _, _ = database
    _publication_schema(conn)
    _, older, first = _publication_save(conn, key='publish-earlier-piece')
    _, newer, second = _publication_save(conn, key='publish-later-piece')
    for row, saved in ((older, first), (newer, second)):
        _rpc(conn, 'piece_set_visibility_v2', dict(p_owner_user_id=_OWNER, p_piece_id=row['id'],
            p_expected_row_version=saved['row_version'], p_visibility_scope='public'))
    assert [p['public_id'] for p in _read_public_feed(conn, _OWNER, limit=1)] == ['piece:' + str(newer['id'])]
    assert [p['public_id'] for p in _read_public_feed(conn, _OWNER, order='oldest', limit=1)] == ['piece:' + str(older['id'])]


_FOLLOW_VISIBILITY = _ROOT / 'supabase/migrations/20261121111000_follow_author_content_visibility.sql'


def _author_visibility_schema(conn, other_author):
    _publication_schema(conn)
    conn.execute('''
        CREATE SCHEMA auth;
        CREATE TABLE auth.users(id uuid PRIMARY KEY);
        CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql AS
            $$ SELECT nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
        GRANT USAGE ON SCHEMA auth TO anon, authenticated;
        CREATE TABLE public.friend_emotion_feed(
            id bigint PRIMARY KEY, viewer_user_id uuid, owner_user_id uuid,
            owner_name text, items jsonb, created_at timestamptz);
        ALTER TABLE public.friend_emotion_feed ENABLE ROW LEVEL SECURITY;
        GRANT SELECT ON public.friend_emotion_feed TO anon, authenticated;
        CREATE POLICY viewer_can_select_own_feed ON public.friend_emotion_feed
            FOR SELECT USING (viewer_user_id=auth.uid());
    ''')
    conn.execute('INSERT INTO auth.users VALUES (%s),(%s),(%s)', (_OWNER,_VIEWER,other_author))
    conn.execute(_FOLLOW_VISIBILITY.read_text())


def _author_visibility_patch(conn, *, author=_OWNER, follower=_VIEWER, pieces=None, emotions=None,
                             role='service_role'):
    return _rpc(conn, 'follow_author_visibility_patch_v1', dict(
        p_author_user_id=author, p_follower_user_id=follower, p_can_view_pieces=pieces,
        p_can_receive_emotion_notifications=emotions), role=role)


def _author_visibility(conn, *, author=_OWNER):
    return _rpc(conn, 'follow_author_visibility_list_v1', dict(p_author_user_id=author))


def _visible_piece_owners(conn, viewer, authors):
    return _rpc(conn, 'follow_piece_visible_owner_ids_v1', dict(p_viewer_user_id=viewer,p_owner_user_ids=authors))


def _emotion_recipients(conn, author, viewers):
    return _rpc(conn, 'emotion_notification_recipients_allowed', dict(p_owner_user_id=author,p_viewer_user_ids=viewers))


def _emotion_feed_rows(conn, viewer, limit=20):
    return _rpc(conn, 'emotion_log_feed_for_viewer', dict(p_viewer_user_id=viewer,p_limit=limit))


def _direct_emotion_feed_ids(conn, viewer):
    with conn.transaction():
        conn.execute('SET LOCAL ROLE authenticated')
        conn.execute("SELECT set_config('request.jwt.claim.sub', %s, true)", (str(viewer),))
        return [row[0] for row in conn.execute('SELECT id FROM public.friend_emotion_feed ORDER BY id').fetchall()]


def test_author_follow_visibility_defaults_preserves_two_independent_choices_and_requires_current_link(database):
    conn, pg, _ = database
    other_author = uuid4()
    _author_visibility_schema(conn, other_author)
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_OWNER, _VIEWER))
    assert _author_visibility(conn) == []
    with pytest.raises(pg.errors.RaiseException, match='(?m)^FOLLOW_RELATION_NOT_FOUND$'):
        _author_visibility_patch(conn, pieces=False)
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s),(%s,%s)',
        (_VIEWER,_OWNER,_VIEWER,other_author))
    default = {'follower_user_id': str(_VIEWER), 'can_view_pieces': True,
               'can_receive_emotion_notifications': True}
    assert _author_visibility(conn) == [default]
    assert _author_visibility(conn,author=other_author) == [default]
    assert conn.execute('SELECT count(*) FROM public.follow_author_visibility_overrides').fetchone()==(0,)
    with pytest.raises(pg.errors.InsufficientPrivilege):
        _author_visibility_patch(conn, pieces=True, role='authenticated')
    with pytest.raises(pg.errors.InsufficientPrivilege):
        _rpc(conn, 'follow_author_visibility_list_v1', dict(p_author_user_id=_OWNER), role='anon')
    with pytest.raises(pg.errors.RaiseException, match='(?m)^FOLLOW_VISIBILITY_INVALID$'):
        _author_visibility_patch(conn)

    assert _author_visibility_patch(conn, pieces=False) == dict(default,can_view_pieces=False)
    assert _author_visibility_patch(conn, emotions=False) == dict(default,can_view_pieces=False,
                                                                 can_receive_emotion_notifications=False)
    assert _author_visibility_patch(conn, pieces=True) == dict(default,can_receive_emotion_notifications=False)
    assert _author_visibility(conn,author=other_author) == [default]
    conn.execute('DELETE FROM public.myprofile_links WHERE viewer_user_id=%s AND owner_user_id=%s', (_VIEWER,_OWNER))
    assert _author_visibility(conn) == []
    assert _visible_piece_owners(conn,_VIEWER,[_OWNER])==[]
    assert _emotion_recipients(conn,_OWNER,[_VIEWER])==[]
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_VIEWER,_OWNER))
    assert _author_visibility(conn) == [dict(default,can_receive_emotion_notifications=False)]
    assert _visible_piece_owners(conn,_VIEWER,[_OWNER])==[str(_OWNER)]
    assert _emotion_recipients(conn,_OWNER,[_VIEWER])==[]
    conn.execute('DELETE FROM auth.users WHERE id=%s', (_VIEWER,))
    assert conn.execute('SELECT count(*) FROM public.follow_author_visibility_overrides').fetchone()==(0,)


def test_author_follow_visibility_bounds_native_legacy_emotion_and_direct_rows(database):
    conn, _, _ = database
    other_author = uuid4()
    _author_visibility_schema(conn, other_author)
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s),(%s,%s)',
        (_VIEWER,_OWNER,_VIEWER,other_author))
    _, piece, saved = _publication_save(conn)
    _rpc(conn, 'piece_set_visibility_v2', dict(p_owner_user_id=_OWNER, p_piece_id=piece['id'],
        p_expected_row_version=saved['row_version'], p_visibility_scope='public'))
    assert _read_public_feed(conn,_VIEWER,target=_OWNER)[0]['body']==piece['piece_text']
    assert set(_visible_piece_owners(conn,_VIEWER,[_OWNER,other_author,_VIEWER]))=={
        str(_OWNER), str(other_author), str(_VIEWER)}
    conn.execute('''
        INSERT INTO public.friend_emotion_feed VALUES
          (1,%s,%s,'synthetic author','[]'::jsonb,'2026-11-21T10:00:00Z'),
          (2,%s,%s,'another synthetic author','[]'::jsonb,'2026-11-21T09:00:00Z'),
          (3,%s,%s,'not the active viewer','[]'::jsonb,'2026-11-21T11:00:00Z')
    ''', (_VIEWER,_OWNER,_VIEWER,other_author,_OWNER,_VIEWER))
    assert _emotion_feed_rows(conn,_VIEWER,limit=1)[0]['id']==1
    assert _direct_emotion_feed_ids(conn,_VIEWER)==[1,2]
    _author_visibility_patch(conn,pieces=False)
    assert _read_public_feed(conn,_VIEWER,target=_OWNER)==[]
    assert _read_public_feed(conn,_OWNER,target=_OWNER)[0]['body']==piece['piece_text']
    assert _visible_piece_owners(conn,_VIEWER,[_OWNER,other_author])==[str(other_author)]
    assert _emotion_recipients(conn,_OWNER,[_VIEWER])==[str(_VIEWER)]
    assert _emotion_feed_rows(conn,_VIEWER,limit=1)[0]['id']==1
    _author_visibility_patch(conn,emotions=False)
    assert _emotion_recipients(conn,_OWNER,[_VIEWER])==[]
    assert _emotion_feed_rows(conn,_VIEWER,limit=1)[0]['id']==2
    assert _direct_emotion_feed_ids(conn,_VIEWER)==[2]
    assert conn.execute('SELECT count(*) FROM public.friend_emotion_feed').fetchone()==(3,)
    _author_visibility_patch(conn,pieces=True)
    assert _read_public_feed(conn,_VIEWER,target=_OWNER)[0]['body']==piece['piece_text']
    assert _direct_emotion_feed_ids(conn,_VIEWER)==[2]


def test_native_resonance_is_atomic_and_rechecks_publication_and_follower_rights(database):
    conn, pg, url = database
    other_viewer = uuid4()
    _author_visibility_schema(conn, other_viewer)
    conn.execute((_ROOT / 'supabase/migrations/20261126070000_piece_v2_resonance.sql').read_text())
    source, piece, saved = _publication_save(conn)
    piece_id = piece['id']
    public_id = 'piece:' + str(piece_id)
    publish = dict(p_owner_user_id=_OWNER, p_piece_id=piece_id, p_expected_row_version=saved['row_version'])
    added = dict(p_viewer_user_id=_VIEWER, p_piece_id=piece_id, p_resonated=True)
    removed = dict(added, p_resonated=False)
    history = dict(p_viewer_user_id=_VIEWER, p_order='newest', p_limit=20, p_offset=0, p_since=None, p_until=None)
    feed = dict(p_viewer_user_id=_VIEWER, p_target_owner_user_id=None, p_following_only=False,
                p_sort='latest', p_limit=20)
    mutate = 'piece_set_resonance_v2'
    read_feed = 'piece_read_resonance_feed_v2'
    read_history = 'piece_read_resonance_history_v2'
    one = {'public_id': public_id, 'resonated': True, 'resonances': 1}
    zero = dict(one, resonated=False, resonances=0)
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_OWNER, _VIEWER))
    with pytest.raises(pg.errors.RaiseException, match='PIECE_NOT_FOUND'):
        _rpc(conn, mutate, added)
    published = _rpc(conn, 'piece_set_visibility_v2', dict(publish, p_visibility_scope='public'))
    with pytest.raises(pg.errors.RaiseException, match='PIECE_NOT_FOUND'):
        _rpc(conn, mutate, added)
    with pytest.raises(pg.errors.RaiseException, match='PIECE_NOT_FOUND'):
        _rpc(conn, mutate, dict(added, p_viewer_user_id=_OWNER))
    conn.execute('INSERT INTO public.myprofile_links VALUES (%s,%s)', (_VIEWER, _OWNER))
    for function, args in ((mutate, added), (read_feed, feed), (read_history, history)):
        for role in ('anon', 'authenticated'):
            with pytest.raises(pg.errors.InsufficientPrivilege):
                _rpc(conn, function, args, role=role)
    assert _parallel(pg, url, [(mutate, added), (mutate, added)]) == [one, one]
    initial = _rpc(conn, read_history, history)
    assert initial['total_items'] == 1
    assert initial['items'][0]['body'] == piece['piece_text']
    assert initial['items'][0]['is_resonated'] is True
    assert _rpc(conn, read_feed, feed)[0]['resonances'] == 1
    assert _rpc(conn, read_feed, dict(feed, p_viewer_user_id=_OWNER))[0]['can_resonate'] is False
    assert _rpc(conn, read_history, dict(history, p_offset=1)) == {'total_items': 1, 'items': []}
    assert _rpc(conn, read_history, dict(history, p_since=datetime(2099, 1, 1, tzinfo=timezone.utc))) == {
        'total_items': 0, 'items': []}
    assert _parallel(pg, url, [(mutate, removed), (mutate, removed)]) == [zero, zero]
    assert _rpc(conn, read_history, history)['items'] == []
    assert _rpc(conn, mutate, added) == one
    assert _rpc(conn, mutate, added) == one
    _author_visibility_patch(conn, pieces=False)
    assert _rpc(conn, read_feed, feed) == []
    assert _rpc(conn, read_history, history)['items'] == []
    with pytest.raises(pg.errors.RaiseException, match='PIECE_NOT_FOUND'):
        _rpc(conn, mutate, removed)
    _author_visibility_patch(conn, pieces=True)
    conn.execute('UPDATE public.emotions SET is_secret=true WHERE id=%s', (source,))
    assert _rpc(conn, read_history, history)['items'] == []
    with pytest.raises(pg.errors.RaiseException, match='PIECE_NOT_FOUND'):
        _rpc(conn, mutate, added)
    conn.execute('UPDATE public.emotions SET is_secret=false WHERE id=%s', (source,))
    _rpc(conn, 'piece_set_visibility_v2', dict(publish, p_expected_row_version=published['row_version'],
                                             p_visibility_scope='private'))
    assert _rpc(conn, read_history, history)['items'] == []
    conn.execute('DELETE FROM auth.users WHERE id=%s', (_VIEWER,))
    assert conn.execute('SELECT count(*) FROM public.piece_record_resonances').fetchone() == (0,)
    assert _used(conn) == 1


def test_native_account_withdrawal_removes_piece_data_and_retries_atomically(database):
    conn, pg, _ = database
    other_owner = uuid4()
    _author_visibility_schema(conn, other_owner)
    conn.execute((_ROOT / 'supabase/migrations/20261126070000_piece_v2_resonance.sql').read_text())
    conn.execute(_ACCOUNT_WITHDRAWAL.read_text())
    conn.execute('INSERT INTO public.profiles VALUES (%s, %s)', (other_owner, 'free'))

    saved, draft, removed = (_preview(conn) for _ in range(3))
    other = _preview(conn, owner=other_owner)
    _save(conn, saved, key='withdrawal-saved')
    _save(conn, removed, key='withdrawal-removed')
    _save(conn, other, key='withdrawal-other', owner=other_owner)
    _rpc(conn, 'piece_delete_v2', _delete_args(removed))
    for record in (saved, other):
        _B2['_insert'](conn, 'piece_export_receipts', dict(
            owner_user_id=record['owner_user_id'], piece_id=record['id'],
            idempotency_key_hash='f'*64, piece_text_hash=record['piece_text_hash'],
            visual_recipe_hash=record['visual_recipe_hash'], outcome='succeeded'))
        _B2['_insert'](conn, 'piece_record_metrics', dict(piece_id=record['id']))
        _B2['_insert'](conn, 'piece_record_reads', dict(piece_id=record['id'], viewer_user_id=_VIEWER))
    _B2['_insert'](conn, 'piece_record_reads', dict(piece_id=other['id'], viewer_user_id=_OWNER))
    for record, viewer in ((saved, _VIEWER), (other, _OWNER), (other, _VIEWER)):
        _B2['_insert'](conn, 'piece_record_resonances', dict(
            piece_id=record['id'], owner_user_id=record['owner_user_id'], viewer_user_id=viewer))

    # Single-Piece deletion keeps its quota debit and idempotency receipt.
    assert _used(conn) == 3
    owner_tables = ('piece_records', 'piece_quota_month_locks', 'piece_quota_consumptions',
                    'piece_export_receipts', 'piece_delete_receipts')

    def owner_counts(owner):
        return tuple(conn.execute('SELECT count(*) FROM public.' + table + ' WHERE owner_user_id=%s',
                                  (owner,)).fetchone()[0] for table in owner_tables)

    assert owner_counts(_OWNER) == (2, 1, 2, 1, 1)
    other_counts = owner_counts(other_owner)
    assert other_counts == (1, 1, 1, 1, 0)

    conn.execute("""CREATE FUNCTION public.synthetic_withdrawal_failure() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_WITHDRAWAL_FAILURE'; END $$""")
    conn.execute("""CREATE TRIGGER synthetic_withdrawal_failure BEFORE DELETE ON public.piece_delete_receipts
        FOR EACH ROW EXECUTE FUNCTION public.synthetic_withdrawal_failure()""")
    with pytest.raises(pg.errors.RaiseException, match='SYNTHETIC_WITHDRAWAL_FAILURE'):
        conn.execute('DELETE FROM auth.users WHERE id=%s', (_OWNER,))
    assert conn.execute('SELECT id FROM auth.users WHERE id=%s', (_OWNER,)).fetchone() == (_OWNER,)
    assert owner_counts(_OWNER) == (2, 1, 2, 1, 1)
    assert owner_counts(other_owner) == other_counts

    conn.execute('DROP TRIGGER synthetic_withdrawal_failure ON public.piece_delete_receipts')
    assert conn.execute('DELETE FROM auth.users WHERE id=%s', (_OWNER,)).rowcount == 1
    assert conn.execute('DELETE FROM auth.users WHERE id=%s', (_OWNER,)).rowcount == 0
    assert owner_counts(_OWNER) == (0, 0, 0, 0, 0)
    assert owner_counts(other_owner) == other_counts
    assert conn.execute('SELECT id FROM public.piece_records ORDER BY id').fetchall() == [(other['id'],)]
    assert conn.execute('SELECT piece_id FROM public.piece_record_metrics').fetchall() == [(other['id'],)]
    for table in ('piece_record_reads', 'piece_record_resonances'):
        assert conn.execute('SELECT piece_id, viewer_user_id FROM public.' + table).fetchall() == [
            (other['id'], _VIEWER),
        ]
    assert conn.execute('SELECT id FROM public.piece_records WHERE id=%s', (draft['id'],)).fetchone() is None
    with pytest.raises(pg.errors.ForeignKeyViolation):
        _preview(conn)
