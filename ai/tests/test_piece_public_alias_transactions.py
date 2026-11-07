"""Verified legacy Piece aliases through current routes and actual isolated SQL.

PGlite serializes requests: these prove atomic statement ownership and overlap
at the application boundary, not independent PostgreSQL connection scheduling.
"""
import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_piece_runtime as api
from piece_generated_identity import generated_instance_aliases
from test_emlis_q2_application import Database, run

ROOT = Path(__file__).parents[2]


@pytest.fixture(scope='module')
def alias_db():
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained PostgreSQL WASM runtime required'
    db = Database()
    ddl = '''
    create table public.mymodel_reflections(
      id uuid primary key, public_id text, owner_user_id uuid not null references auth.users,
      q_key text, question text, source_type text, is_active boolean, status text);
    create table public.mymodel_qna_metrics(q_key text not null, q_instance_id text,
      views bigint not null default 0, resonances bigint not null default 0,
      updated_at timestamptz not null default now());
    create unique index mymodel_qna_metrics_unique_global on public.mymodel_qna_metrics(q_key)
      where q_instance_id is null;
    create unique index mymodel_qna_metrics_unique_instance on public.mymodel_qna_metrics(q_instance_id)
      where q_instance_id is not null;
    create table public.mymodel_qna_resonances(viewer_user_id uuid references auth.users,
      q_instance_id text, q_key text not null, created_at timestamptz not null default now(),
      primary key(viewer_user_id,q_instance_id));
    create table public.mymodel_qna_echoes(viewer_user_id uuid references auth.users,
      q_instance_id text, target_user_id uuid not null references auth.users, question_id int not null,
      q_key text not null, strength text not null check(strength in ('small','medium','large')),
      memo text, context_source_type text, context_question text, context_answer text,
      context_topic_key text, context_category text, created_at timestamptz not null default now(),
      primary key(viewer_user_id,q_instance_id));
    -- Existing publish/maintenance paths already require source UPDATE.
    grant select,update on public.mymodel_reflections to service_role;
    grant select,insert,update,delete on public.mymodel_qna_resonances,public.mymodel_qna_echoes to service_role;
    grant select,insert,update on public.mymodel_qna_metrics to service_role;
    '''
    for suffix in ('piece_legacy_metrics_atomic.sql', 'piece_legacy_reaction_alias.sql'):
        migrations = sorted((ROOT / 'supabase/migrations').glob('*_' + suffix))
        assert len(migrations) == 1, 'exactly one canonical migration is required: ' + suffix
        ddl += migrations[0].read_text()
    with db.lock:
        db.proc.stdin.write(json.dumps({'sql': ddl, 'script': True})+'\n'); db.proc.stdin.flush()
        result = json.loads(db.proc.stdout.readline())
    assert 'code' not in result, result
    yield db
    db.proc.stdin.close(); db.proc.wait(timeout=10)


@pytest.fixture
def case(alias_db, monkeypatch):
    db = alias_db
    owner, viewer, other, source_id = (str(uuid4()) for _ in range(4))
    key = 'generated:key:' + source_id
    public_id = 'public-' + source_id
    for uid in (owner, viewer, other):
        assert 'code' not in db.query('insert into auth.users values ($1)', [uid])
    assert 'code' not in db.query('insert into public.mymodel_reflections values($1,$2,$3,$4,$5,$6,true,$7)',
          [source_id, public_id, owner, key, '公開の問い', 'emotion_generated', 'published'])
    row = dict(id=source_id, public_id=public_id, owner_user_id=owner, q_key=key,
               source_type='emotion_generated', question='公開の問い')
    aliases = generated_instance_aliases(row); canonical = aliases[0]
    state = dict(viewer=viewer, owner=owner, other=other, row=row, aliases=aliases,
                 iid=canonical, key=key, calls=[], denied=False, followed=True)
    async def resolve(token): return state['viewer']
    async def access(**kwargs):
        if state['denied'] or kwargs['q_instance_id'] not in aliases:
            raise HTTPException(status_code=404, detail='Reflection not found')
        return row
    async def following(**kwargs): return {owner} if state['followed'] else set()
    async def noop(*args, **kwargs): return None
    async def rpc(name, payload):
        assert name == 'piece_apply_legacy_reaction'
        state['calls'].append(dict(payload))
        await asyncio.sleep(0)
        args = ','.join(f'{k}=>${i}' for i,k in enumerate(payload,1))
        values = [json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
        result = await asyncio.to_thread(db.query, f'select public.{name}({args}) as value', values,
                                         'service_role', error_message=True)
        return httpx.Response(400 if 'code' in result else 200,
                              json=result if 'code' in result else result['rows'][0]['value'])
    async def forbidden(*args, **kwargs):
        raise AssertionError('reaction state/counters must share the one authorized RPC')
    monkeypatch.setattr(api, '_resolve_user_id_from_token', resolve)
    monkeypatch.setattr(api, 'resolve_generated_reflection_access', access)
    monkeypatch.setattr(api, 'get_public_generated_reflection_text', lambda _: '公開用に検査済みの本文。')
    monkeypatch.setattr(api, '_fetch_followed_owner_ids', following)
    monkeypatch.setattr(api, '_sb_post_rpc', rpc)
    for name in ('_is_resonated', '_sb_post', '_sb_delete', '_inc_metric'):
        monkeypatch.setattr(api, name, forbidden)
    for name in ('enqueue_global_snapshot_refresh','enqueue_ranking_board_refresh',
                 'enqueue_account_status_refresh','enqueue_global_summary_refresh',
                 'enqueue_global_summary_refresh_many'):
        monkeypatch.setattr(api, name, noop)
    app = FastAPI(); api.register_piece_runtime_routes(app)
    state.update(db=db, app=app)
    return state


async def reaction(c, operation, iid=None, **values):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=c['app']),base_url='http://local') as client:
        return await client.post('/piece/'+operation, headers={'Authorization':'Bearer synthetic'},
                    json=dict(q_instance_id=iid or c['iid'], **values))


def rows(c, table):
    return c['db'].query('select * from public.'+table+' where '+
        ('q_key=$1' if table=='mymodel_qna_metrics' else 'viewer_user_id=$1'),
        [c['key'] if table=='mymodel_qna_metrics' else c['viewer']])['rows']


def seed_reaction(c, iid, viewer=None):
    viewer = viewer or c['viewer']
    assert 'code' not in c['db'].query('insert into public.mymodel_qna_resonances(viewer_user_id,q_instance_id,q_key) values($1,$2,$3)',[viewer,iid,c['key']])
    result = c['db'].query('select public.piece_increment_legacy_metric($1,$2,$3,1)',[c['key'],iid,'resonances'],'service_role')
    assert 'code' not in result, result


def seed_echo(c, iid):
    assert 'code' not in c['db'].query('insert into public.mymodel_qna_echoes(viewer_user_id,q_instance_id,target_user_id,question_id,q_key,strength,memo) values($1,$2,$3,0,$4,$5,$6)',
            [c['viewer'],iid,c['owner'],c['key'],'small','旧メモ'])


@pytest.mark.parametrize('operation',['resonance','resonances/submit'])
def test_different_aliases_share_one_new_reaction_and_counter(case, operation):
    c=case
    async def both():
        return await asyncio.gather(*(reaction(c,operation,iid,**({'strength':'medium'} if operation.endswith('submit') else {}))
                                   for iid in (c['aliases'][0],c['aliases'][2])))
    responses=run(both())
    assert [r.status_code for r in responses]==[200,200], [r.text for r in responses]
    assert all(r.json()['q_instance_id']==c['iid'] for r in responses)
    assert [r['q_instance_id'] for r in rows(c,'mymodel_qna_resonances')]==[c['iid']]
    assert all(r['resonances']==1 for r in rows(c,'mymodel_qna_metrics'))
    assert all(p['p_canonical_id']==c['iid'] and p['p_source_id']==c['row']['id'] for p in c['calls'])
    assert all('alias' not in k for p in c['calls'] for k in p), 'SQL derives aliases from its verified row'


@pytest.mark.parametrize('operation',['resonance','resonances/submit'])
def test_existing_legacy_alias_never_readds_or_duplicates_echo(case, operation):
    c=case; old='reflection:'+c['row']['id']; seed_reaction(c,old); seed_echo(c,old)
    response=run(reaction(c,operation,**({'strength':'large','memo':'新しい原文'} if operation.endswith('submit') else {})))
    assert response.status_code==200,response.text
    assert response.json()['resonances']==1
    assert [r['q_instance_id'] for r in rows(c,'mymodel_qna_resonances')]==[old]
    echoes=rows(c,'mymodel_qna_echoes')
    assert len(echoes)==1 and echoes[0]['q_instance_id']==old
    if operation.endswith('submit'):
        assert echoes[0]['memo']=='新しい原文' and echoes[0]['strength']=='large'
    assert all(r['resonances']==1 for r in rows(c,'mymodel_qna_metrics'))


def test_remove_undoes_every_own_legacy_alias_and_preserves_other_viewer(case):
    c=case; old='reflection:'+c['row']['id']
    for iid in (old,c['iid']): seed_reaction(c,iid); seed_echo(c,iid)
    seed_reaction(c,c['iid'],viewer=c['other'])
    responses=run(asyncio_gather_remove(c,old))
    assert [r.status_code for r in responses]==[200,200], [r.text for r in responses]
    assert rows(c,'mymodel_qna_resonances')==[] and rows(c,'mymodel_qna_echoes')==[]
    metrics=rows(c,'mymodel_qna_metrics')
    assert next(r for r in metrics if r['q_instance_id'] is None)['resonances']==1
    assert sum(r['resonances'] for r in metrics if r['q_instance_id'] is not None)==1
    assert c['db'].query('select count(*)::int as n from public.mymodel_qna_resonances where viewer_user_id=$1',[c['other']])['rows']==[{'n':1}]


async def asyncio_gather_remove(c,old):
    return await asyncio.gather(reaction(c,'resonances/delete',old),reaction(c,'resonances/delete'))


@pytest.mark.parametrize('existing',[False,True])
@pytest.mark.parametrize('add_operation',['resonance','resonances/submit'])
def test_parallel_add_remove_keeps_state_and_counters_in_one_commit(case, existing, add_operation):
    c=case; old='reflection:'+c['row']['id']
    if existing: seed_reaction(c,old)
    async def both():
        return await asyncio.gather(reaction(c,add_operation,old,**({'strength':'medium','memo':'並行更新'} if add_operation.endswith('submit') else {})),
                                    reaction(c,'resonances/delete'))
    responses=run(both())
    assert [r.status_code for r in responses]==[200,200], [r.text for r in responses]
    remaining=len(rows(c,'mymodel_qna_resonances'))
    metrics=rows(c,'mymodel_qna_metrics')
    assert remaining in (0,1)
    assert next(r for r in metrics if r['q_instance_id'] is None)['resonances']==remaining
    assert sum(r['resonances'] for r in metrics if r['q_instance_id'] is not None)==remaining


def test_bad_stored_key_rolls_back_the_whole_echo_and_reaction(case):
    c=case; seed_echo(c,c['iid'])
    c['db'].query('insert into public.mymodel_qna_metrics(q_key,q_instance_id,resonances) values($1,$2,1)', ['wrong-key',c['iid']])
    before=rows(c,'mymodel_qna_echoes')
    response=run(reaction(c,'resonances/submit',strength='large',memo='must not overwrite'))
    assert response.status_code==502
    assert rows(c,'mymodel_qna_echoes')==before and rows(c,'mymodel_qna_resonances')==[]
    assert rows(c,'mymodel_qna_metrics')==[]


@pytest.mark.parametrize('change,expected',[('denied',404),('unfollow',403),('self',400)])
def test_route_permissions_reject_before_sql(case,change,expected):
    c=case
    if change=='denied':c['denied']=True
    elif change=='unfollow':c['followed']=False
    else:c['viewer']=c['owner']
    response=run(reaction(c,'resonance'))
    assert response.status_code==expected,response.text
    assert c['calls']==[]


@pytest.mark.parametrize('field,value',[('p_source_id',str(uuid4())),('p_expected_owner',str(uuid4())),
                                       ('p_canonical_id','reflection:unrelated'),('p_q_key','forged-key')])
def test_sql_rechecks_verified_row_identity_without_arbitrary_aliases(case,field,value):
    c=case
    params=dict(p_source_id=c['row']['id'],p_expected_owner=c['owner'],p_viewer_id=c['viewer'],
                p_canonical_id=c['iid'],p_q_key=c['key'],p_operation='resonate',p_echo=None)
    params[field]=value
    args=','.join(f'{k}=>${i}' for i,k in enumerate(params,1))
    result=c['db'].query('select public.piece_apply_legacy_reaction('+args+')',list(params.values()),'service_role')
    assert result['code']=='P0001',result
    assert rows(c,'mymodel_qna_resonances')==[] and rows(c,'mymodel_qna_metrics')==[]


def test_new_reaction_rpc_is_service_only_and_not_security_definer(alias_db):
    row=alias_db.query("select prosecdef,proconfig,has_function_privilege('anon',p.oid,'execute') as anon_exec,"
        "has_function_privilege('authenticated',p.oid,'execute') as auth_exec,"
        "has_function_privilege('service_role',p.oid,'execute') as service_exec from pg_proc p "
        "where p.oid='public.piece_apply_legacy_reaction(uuid,uuid,uuid,text,text,text,jsonb)'::regprocedure")['rows'][0]
    assert row==dict(prosecdef=False,proconfig=['search_path=pg_catalog'],anon_exec=False,auth_exec=False,service_exec=True)


def test_legacy_alias_history_lookup_maps_the_verified_row_and_keeps_uuid_filter_typed(case,monkeypatch):
    c=case; calls=[]
    async def get(path,*,params):
        calls.append(dict(params))
        if 'id' in params:
            values=json.loads('['+params['id'][4:-1]+']')
            from uuid import UUID
            assert all(str(UUID(v))==v for v in values)
        return [dict(c['row'],is_active=True,status='published')]
    monkeypatch.setattr(api,'_sb_get_json_local',get)
    ids=set(c['aliases'])|{'legacy-owner:123'}
    mapped=run(api._fetch_generated_reflections_by_public_ids(ids))
    assert set(mapped)==set(c['aliases'])
    assert all(r['id']==c['row']['id'] for r in mapped.values())
    assert len(calls)==2


def test_saved_generated_history_folds_aliases_without_losing_counts_or_read_state(case,monkeypatch):
    import piece_public_read_store as store
    c=case; old='reflection:'+c['row']['id']; seed_reaction(c,old)
    c['db'].query('update public.mymodel_qna_metrics set views=7 where q_key=$1',[c['key']])
    with c['db'].lock:
        c['db'].proc.stdin.write(json.dumps({'script':True,'sql':
          'create table if not exists public.mymodel_qna_reads(viewer_user_id uuid,q_instance_id text,viewed_at timestamptz default now(),primary key(viewer_user_id,q_instance_id));'})+'\n')
        c['db'].proc.stdin.flush(); assert 'code' not in json.loads(c['db'].proc.stdout.readline())
    c['db'].query('insert into public.mymodel_qna_reads(viewer_user_id,q_instance_id) values($1,$2)',[c['viewer'],c['row']['id']])
    async def source_get(path,*,params):return [dict(c['row'],is_active=True,status='published')]
    async def profiles(ids):return {c['owner']:{'display_name':'旧alias所有者'}}
    async def state_get(path,*,params):
        values=json.loads('['+params['q_instance_id'][4:-1]+']')
        marks=','.join('$'+str(i+1) for i in range(len(values)))
        if path.endswith('/'+store.METRICS_READ_TABLE):
            table,columns='mymodel_qna_metrics','q_instance_id,q_key,views::int,resonances::int'
        else:
            assert path.endswith('/'+store.READS_READ_TABLE)
            table,columns='mymodel_qna_reads','q_instance_id'
        args=list(values);where='q_instance_id in ('+marks+')'
        if 'viewer_user_id' in params:
            args.append(params['viewer_user_id'][3:]);where+=' and viewer_user_id=$'+str(len(args))
        result=c['db'].query('select '+columns+' from public.'+table+' where '+where,args)
        assert 'code' not in result,result
        return httpx.Response(200,json=result['rows'])
    monkeypatch.setattr(api,'_sb_get_json_local',source_get)
    monkeypatch.setattr(api,'_fetch_profiles_by_ids',profiles)
    monkeypatch.setattr(store,'sb_get',state_get)
    items=run(api._build_saved_generated_items(prepared_rows=[
        (old,c['owner'],'2026-11-07T02:00:00Z'),(c['iid'],c['owner'],'2026-11-07T01:00:00Z')],
        viewer_user_id=c['viewer'],followed_owner_ids={c['owner']}))
    assert len(items)==1
    item=items[0]
    assert item.q_instance_id==c['iid'] and item.saved_at=='2026-11-07T02:00:00Z'
    assert item.views==7 and item.resonances==1 and item.is_new is False
    assert item.body=='公開用に検査済みの本文。'


def test_counter_failure_rolls_back_echo_and_reaction_state(case):
    c=case
    trigger_name='test_counter_'+c['row']['id'].replace('-','')
    key_literal=c['key'].replace("'","''")
    sql=f'''create function public.{trigger_name}() returns trigger language plpgsql as $$
      begin if new.q_key='{key_literal}' then raise exception 'synthetic counter unavailable'; end if; return new; end; $$;
      create trigger {trigger_name} before insert or update on public.mymodel_qna_metrics
      for each row execute function public.{trigger_name}();'''
    with c['db'].lock:
        c['db'].proc.stdin.write(json.dumps({'script':True,'sql':sql})+'\n');c['db'].proc.stdin.flush()
        assert 'code' not in json.loads(c['db'].proc.stdout.readline())
    try:
        response=run(reaction(c,'resonances/submit',strength='large',memo='原文保持'))
        assert response.status_code==502
        assert rows(c,'mymodel_qna_echoes')==[] and rows(c,'mymodel_qna_resonances')==[]
        assert rows(c,'mymodel_qna_metrics')==[]
    finally:
        with c['db'].lock:
            c['db'].proc.stdin.write(json.dumps({'script':True,'sql':f'drop trigger {trigger_name} on public.mymodel_qna_metrics; drop function public.{trigger_name}();'})+'\n')
            c['db'].proc.stdin.flush();assert 'code' not in json.loads(c['db'].proc.stdout.readline())


@pytest.mark.parametrize('change',["is_active=false", "status='draft'", 'owner_user_id=NULL'])
def test_rpc_rechecks_source_after_an_old_api_read(case,change):
    c=case
    if change=='owner_user_id=NULL':
        change='owner_user_id=\''+c['other']+'\''
    c['db'].query('update public.mymodel_reflections set '+change+' where id=$1',[c['row']['id']])
    response=run(reaction(c,'resonance'))  # Access fixture retains the earlier authorized row.
    assert response.status_code==502
    assert rows(c,'mymodel_qna_resonances')==[] and rows(c,'mymodel_qna_metrics')==[]


def test_history_metadata_lookup_does_not_truncate_large_alias_batches(case,monkeypatch):
    c=case; corpus=[];calls=[]
    for _ in range(512):
        rid=str(uuid4())
        corpus.append(dict(id=rid,public_id=str(uuid4()),owner_user_id=str(uuid4()),
            q_key='generated:'+rid,question='保存済みの問い'+rid,
            source_type='emotion_generated',status='published',is_active=True))
    async def get(path,*,params):
        field='id' if 'id' in params else 'public_id'
        values=json.loads('['+params[field][4:-1]+']')
        calls.append((field,len(values)))
        assert len(values)<=200 and int(params['limit'])<=600
        return [row for row in corpus if row[field] in values]
    monkeypatch.setattr(api,'_sb_get_json_local',get)
    monkeypatch.setattr(api,'get_public_generated_reflection_text',lambda row:'保存済み本文'+row['id'])
    ids={row['id'] for row in corpus}
    mapped=run(api._fetch_generated_reflections_by_public_ids(ids))
    assert set(mapped)==ids
    assert [size for field,size in calls if field=='id']==[200,200,112]
    assert sum(size for field,size in calls if field=='public_id')==1024


@pytest.mark.parametrize('name',['METRICS_TABLE','RESONANCES_TABLE','ECHOES_TABLE','MYMODEL_REFLECTIONS_TABLE'])
def test_custom_physical_table_cannot_silently_write_the_canonical_store(case,monkeypatch,name):
    c=case;monkeypatch.setattr(api,name,'custom_legacy_table')
    response=run(reaction(c,'resonance'))
    assert response.status_code==502 and c['calls']==[]
    assert rows(c,'mymodel_qna_resonances')==[] and rows(c,'mymodel_qna_metrics')==[]
