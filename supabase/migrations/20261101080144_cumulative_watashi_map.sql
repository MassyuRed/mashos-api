-- Cumulative maps share the existing immutable artifact, not a re-analysis of
-- a past month. Monthly references freeze the first successful capture in JST.
begin;
alter table public.analysis_observed_artifacts
  add column source_profile text not null default 'period.v1'
    check (source_profile in ('period.v1','cumulative.v1')),
  drop constraint analysis_observed_artifacts_source_guard_check,
  add constraint analysis_observed_artifacts_source_guard_check
    check (source_guard ~ '^analysis-db-(v1|compare-v1|cumulative-v1):[0-9a-f]{64}$');
-- Keep the period artifact's old size policy; cumulative input is not truncated
-- or rejected merely because its complete evidence exceeds that old bound.
do $$ declare c record; begin
  for c in select conname from pg_constraint where conrelid='public.analysis_observed_artifacts'::regclass
    and contype='c' and pg_get_constraintdef(oid) like '%octet_length%' loop
    execute format('alter table public.analysis_observed_artifacts drop constraint %I',c.conname);
  end loop;
end; $$;
alter table public.analysis_observed_artifacts add constraint analysis_period_artifact_size
  check (source_profile='cumulative.v1' or
    octet_length(private_evidence::text)+octet_length(safe_projection::text)+octet_length(content_text)<=2097152);
alter table public.analysis_observed_artifacts add constraint analysis_artifact_owner_identity unique(id,user_id);

create table public.analysis_cumulative_months (
  user_id uuid not null references auth.users(id) on delete cascade,
  snapshot_month date not null check (extract(day from snapshot_month)=1),
  artifact_id uuid not null,
  captured_at timestamptz not null default statement_timestamp(),
  primary key(user_id,snapshot_month),
  foreign key(artifact_id,user_id) references public.analysis_observed_artifacts(id,user_id) on delete cascade
);
alter table public.analysis_cumulative_months enable row level security;
revoke all on public.analysis_cumulative_months from public,anon,authenticated,service_role;
grant select,insert,delete on public.analysis_cumulative_months to service_role;
create index analysis_cumulative_artifact_month on public.analysis_cumulative_months(artifact_id);

-- One MVCC statement, with no plan retention or latest-N truncation. Generated
-- replies never become original input. Tier/clock do not change source identity.
create function public.analysis_cumulative_source_snapshot(p_user_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare members jsonb; identity_members jsonb; tier text; instant timestamptz:=statement_timestamp(); first_at timestamptz;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  if not found or tier not in ('free','plus','premium') then
    raise sqlstate '42501' using message='analysis_owner_unavailable'; end if;
  select coalesce(jsonb_agg(jsonb_build_object('original',public.emlis_parent_source(e),
    'thread',case when t.id is null then null else jsonb_build_object(
      'id',t.id,'user_id',t.user_id,'original_emotion_id',t.original_emotion_id,
      'source_snapshot',t.source_snapshot,'revision',t.revision,'issued_count',t.issued_count,
      'started_question_limit',t.started_question_limit,'data',jsonb_strip_nulls(jsonb_build_object(
        'runtime_profile',t.data->'runtime_profile','semantic_profile',t.data->'semantic_profile',
        'execution_mode',t.data->'execution_mode','original_source_ref',t.data->'original_source_ref'))) end,
    'events',coalesce((select jsonb_agg(jsonb_build_object('id',v.id,'thread_id',v.thread_id,
      'kind',v.kind,'round_index',v.round_index,'question_id',v.question_id,'payload',v.payload) order by v.seq)
      from public.emlis_thread_events v where v.thread_id=t.id and v.kind in ('QUESTION','ANSWER')),'[]'::jsonb))
    order by e.created_at,e.id),'[]'::jsonb), min(e.created_at at time zone 'UTC')
    into members,first_at
    from public.emotions e left join public.emlis_input_threads t on t.original_emotion_id=e.id
    where e.user_id=p_user_id and e.created_at < instant at time zone 'UTC';
  select coalesce(jsonb_agg(m #- '{thread,revision}' order by ord),'[]'::jsonb) into identity_members
    from jsonb_array_elements(members) with ordinality as x(m,ord);
  return jsonb_build_object('tier',tier,'now',instant,'members',members,
    'period_start',coalesce(first_at,instant-interval '1 second'),'period_end',instant,
    'guard','analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      jsonb_build_object('owner',p_user_id,'members',identity_members)::text,'UTF8')),'hex'));
end;
$$;

-- Generation and first-of-month capture are atomic. No change of plan deletes
-- the artifact or its month references. Reused current artifacts can be captured
-- in a later month without changing their original analysis timestamp/bytes.
create function public.analysis_cumulative_commit(p_user_id uuid,p_guard text,
  p_artifact_id text default null,p_private_evidence jsonb default null,
  p_projection jsonb default null,p_text text default null,
  p_start timestamptz default null,p_end timestamptz default null,p_existing_id uuid default null,p_force boolean default false)
returns uuid language plpgsql volatile security definer set search_path='' as $$
declare snap jsonb; rid uuid; month_key date;
begin
  if current_setting('transaction_isolation') <> 'read committed' then
    raise sqlstate '40001' using message='analysis_isolation_unavailable'; end if;
  -- Serialize commits for the same owner before looking up/reusing a guard.
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002' using message='analysis_owner_unavailable'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events
    in share mode nowait;
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  if snap->>'guard' is distinct from p_guard then
    raise sqlstate '40001' using message='analysis_source_changed'; end if;
  select id into rid from public.analysis_observed_artifacts where user_id=p_user_id
    and source_profile='cumulative.v1' and source_guard=p_guard
    order by generated_at desc,id desc limit 1;
  if p_existing_id is not null and rid is distinct from p_existing_id then
    raise sqlstate '40001' using message='analysis_source_changed'; end if;
  if p_force or rid is null then
    if p_artifact_id is null or p_artifact_id !~ '^artifact:[0-9a-f]{32}$'
      or p_start is distinct from (snap->>'period_start')::timestamptz
      or p_end is null or p_end>statement_timestamp() or p_end<=p_start
      or p_private_evidence->'coverage'->>'profile' is distinct from 'cumulative.v1'
      or (p_private_evidence->'coverage'->>'source_count')::integer is distinct from jsonb_array_length(snap->'members') then
      raise sqlstate '22023' using message='analysis_cumulative_artifact_invalid'; end if;
    rid:=substring(p_artifact_id from 10)::uuid;
    insert into public.analysis_observed_artifacts(id,artifact_id,artifact_version,user_id,
      report_type,report_mode,access_tier,period_start,period_end,source_guard,
      private_evidence,safe_projection,content_text,source_profile)
    values(rid,p_artifact_id,1,p_user_id,'latest','standard',snap->>'tier',p_start,p_end,p_guard,
      p_private_evidence,p_projection,p_text,'cumulative.v1');
  end if;
  month_key:=date_trunc('month',statement_timestamp() at time zone 'Asia/Tokyo')::date;
  insert into public.analysis_cumulative_months(user_id,snapshot_month,artifact_id)
    values(p_user_id,month_key,rid) on conflict(user_id,snapshot_month) do nothing;
  -- Only the current map and actual monthly references are durable products.
  -- Discard superseded, unreferenced current caches instead of storing one
  -- full cumulative evidence copy for every historical refresh.
  delete from public.analysis_observed_artifacts a where a.user_id=p_user_id
    and a.source_profile='cumulative.v1' and a.id<>rid
    and not exists(select 1 from public.analysis_cumulative_months m where m.artifact_id=a.id);
  return rid;
exception when lock_not_available or deadlock_detected then
  raise sqlstate '40001' using message='analysis_source_busy';
end;
$$;

-- Rank the complete month collection BEFORE pagination or id filtering. The
-- same entitlement set is used by list/detail/evidence; an old current ID is
-- never a way around the monthly window. No source reconciliation on history.
create function public.analysis_cumulative_read(p_user_id uuid,p_id uuid default null,
  p_history boolean default false,p_limit integer default 60,p_offset integer default 0,
  p_month date default null,p_metadata_only boolean default false)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare snap jsonb; tier text; max_months integer; current_id uuid; items jsonb;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  if not found or tier not in ('free','plus','premium') then
    raise sqlstate '42501' using message='analysis_owner_unavailable'; end if;
  max_months:=case tier when 'free' then 2 when 'plus' then 12 else null end;
  if p_limit not between 1 and 200 or p_offset not between 0 and 10000 then
    raise sqlstate '22023' using message='analysis_page_invalid'; end if;
  if not p_history and p_month is null then
    snap:=public.analysis_cumulative_source_snapshot(p_user_id);
    select id into current_id from public.analysis_observed_artifacts where user_id=p_user_id
      and source_profile='cumulative.v1' and source_guard=snap->>'guard'
      order by generated_at desc,id desc limit 1;
  end if;
  with ranked as (
    select m.*,row_number() over(order by snapshot_month desc) as n
      from public.analysis_cumulative_months m where m.user_id=p_user_id
  ), visible as (
    select r.artifact_id as id,r.snapshot_month,r.captured_at,'monthly'::text as kind
      from ranked r where (max_months is null or r.n<=max_months)
      and (p_month is null or r.snapshot_month=p_month)
      and (p_history or p_id is not null)
    union all
    select current_id,null::date,null::timestamptz,'latest'::text
      where current_id is not null and not p_history and p_month is null
  ), page as (
    select a.*,v.snapshot_month,v.captured_at,v.kind
    from visible v join public.analysis_observed_artifacts a on a.id=v.id and a.user_id=p_user_id
    where (p_id is null or a.id=p_id)
    order by v.snapshot_month desc nulls last,a.generated_at desc,a.id desc
    limit p_limit offset p_offset
  ) select coalesce(jsonb_agg(jsonb_build_object('id',id,'report_type',kind,
    'report_mode','standard','title','わたしマップ','period_start',period_start,'period_end',period_end,
    'generated_at',generated_at,'updated_at',generated_at,'snapshot_month',snapshot_month,
    'captured_at',captured_at,'source_profile','cumulative.v1') ||
    case when p_metadata_only then '{}'::jsonb else jsonb_build_object('content_text',content_text,
      'content_json',jsonb_build_object('report_mode','standard','watashiMap',safe_projection,
      'map_context',private_evidence->'coverage')) end
    order by snapshot_month desc nulls last,generated_at desc,id desc),'[]'::jsonb) into items from page;
  return jsonb_build_object('items',items,'subscription_tier',tier,'matched',
    exists(select 1 from public.analysis_observed_artifacts where user_id=p_user_id
      and source_profile='cumulative.v1' and id=p_id),'history_limit',max_months);
end;
$$;

-- An evidence read is scoped to an authorized map and one of its nodes. It
-- opens no general old-input history. Edits are marked rather than passed off
-- as the original version used by the saved analysis.
create function public.analysis_cumulative_evidence(p_user_id uuid,p_id uuid,p_node text,p_month date default null)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare permitted jsonb; node jsonb; result jsonb;
begin
  permitted:=public.analysis_cumulative_read(p_user_id,p_id,false,1,0,p_month);
  if jsonb_array_length(permitted->'items')=0 then
    raise sqlstate 'P0002' using message='analysis_report_unavailable'; end if;
  select n into node from public.analysis_observed_artifacts a,
    jsonb_array_elements(a.private_evidence->'graph'->'nodes') n
    where a.id=p_id and a.user_id=p_user_id and n->>'node_ref'=p_node;
  if node is null then raise sqlstate 'P0002' using message='analysis_evidence_unavailable'; end if;
  select coalesce(jsonb_agg(jsonb_build_object('original',public.emlis_parent_source(e),
    'thread',case when t.id is null then null else to_jsonb(t) end,
    'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq) from public.emlis_thread_events v
      where v.thread_id=t.id and v.kind in ('QUESTION','ANSWER')),'[]'::jsonb),
    'expected_envelopes',(select coalesce(jsonb_agg(distinct r->>'source_envelope_id'),'[]'::jsonb)
      from jsonb_array_elements(node->'evidence_refs') r
      where s->'child_source_envelope_refs' ? (r->>'source_envelope_id')),
    'analyzed_version',s->>'saved_record_version') order by e.created_at,e.id),'[]'::jsonb)
    into result from public.emotions e left join public.emlis_input_threads t on t.original_emotion_id=e.id
    join public.analysis_observed_artifacts a on a.id=p_id,
    jsonb_array_elements(a.private_evidence->'source_members') s
    where e.user_id=p_user_id and a.user_id=p_user_id and node->'record_refs' ? e.id::text
      and s->>'saved_record_ref'=e.id::text;
  return jsonb_build_object('items',result,'tier',permitted->>'subscription_tier','now',statement_timestamp());
end;
$$;

-- Keep the existing period lifecycle, but never let it delete cumulative rows.
-- A plan change preserves all saved monthly data, including legacy period rows.
create or replace function public.analysis_observed_invalidate() returns trigger
language plpgsql security definer set search_path='' as $$
declare owner_id uuid; input_id uuid; ts timestamp; row_data jsonb;
begin
  if TG_OP='UPDATE' then
    if to_jsonb(OLD)=to_jsonb(NEW) then return null; end if;
    if TG_TABLE_NAME='profiles' then return null; end if;
  end if;
  for row_data in select value from jsonb_array_elements(
    case when TG_OP='INSERT' then jsonb_build_array(to_jsonb(NEW))
         when TG_OP='DELETE' then jsonb_build_array(to_jsonb(OLD))
         else jsonb_build_array(to_jsonb(OLD),to_jsonb(NEW)) end) loop
    if TG_TABLE_NAME='emotions' then
      owner_id:=(row_data->>'user_id')::uuid; input_id:=(row_data->>'id')::uuid;
      ts:=(row_data->>'created_at')::timestamp;
    elsif TG_TABLE_NAME='profiles' then
      delete from public.analysis_observed_artifacts where user_id=(row_data->>'id')::uuid;
      continue;
    else
      if TG_TABLE_NAME='emlis_input_threads' then
        input_id:=(row_data->>'original_emotion_id')::uuid; owner_id:=(row_data->>'user_id')::uuid;
      else
        select original_emotion_id,user_id into input_id,owner_id from public.emlis_input_threads
          where id=(row_data->>'thread_id')::uuid;
      end if;
      select created_at into ts from public.emotions where id=input_id;
    end if;
    delete from public.analysis_observed_artifacts a where a.user_id=owner_id and (
      (a.source_profile='period.v1' and (
        (ts at time zone 'UTC'>=a.period_start and ts at time zone 'UTC'<a.period_end)
        or (TG_TABLE_NAME='emotions' and a.report_type='latest')
        or (ts at time zone 'UTC'>=(a.private_evidence->'comparison_dependency'->>'previous_period_start')::timestamptz
          and ts at time zone 'UTC'<(a.private_evidence->'comparison_dependency'->>'previous_period_end')::timestamptz)))
      or (a.source_profile='cumulative.v1' and (TG_OP='DELETE'
        or (TG_TABLE_NAME='emotions' and TG_OP='UPDATE'
          and to_jsonb(OLD)->>'user_id' is distinct from to_jsonb(NEW)->>'user_id'))
        and ((a.private_evidence->'source_record_refs') ? input_id::text
          or exists(select 1 from jsonb_array_elements(a.private_evidence->'source_members') s
            where s->>'saved_record_ref'=input_id::text))));
  end loop;
  return null;
end;
$$;

revoke all on function public.analysis_cumulative_source_snapshot(uuid),
  public.analysis_cumulative_commit(uuid,text,text,jsonb,jsonb,text,timestamptz,timestamptz,uuid,boolean),
  public.analysis_cumulative_read(uuid,uuid,boolean,integer,integer,date,boolean),
  public.analysis_cumulative_evidence(uuid,uuid,text,date) from public,anon,authenticated,service_role;
grant execute on function public.analysis_cumulative_source_snapshot(uuid),
  public.analysis_cumulative_commit(uuid,text,text,jsonb,jsonb,text,timestamptz,timestamptz,uuid,boolean),
  public.analysis_cumulative_read(uuid,uuid,boolean,integer,integer,date,boolean),
  public.analysis_cumulative_evidence(uuid,uuid,text,date) to service_role;
commit;
