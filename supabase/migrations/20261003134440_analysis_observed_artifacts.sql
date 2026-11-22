-- One private immutable Analysis store. Legacy reports remain untouched.
begin;
create table public.analysis_observed_artifacts (
  id uuid primary key,
  artifact_id text not null unique check (artifact_id = 'artifact:' || replace(id::text,'-','')),
  artifact_version integer not null check (artifact_version = 1),
  user_id uuid not null references auth.users(id) on delete cascade,
  report_type text not null check (report_type in ('latest','monthly')),
  report_mode text not null check (report_mode in ('light','standard','deep')),
  access_tier text not null check (access_tier in ('free','plus','premium')),
  period_start timestamptz not null,
  period_end timestamptz not null check (period_end > period_start),
  source_guard text not null check (source_guard ~ '^analysis-db-v1:[0-9a-f]{64}$'),
  private_evidence jsonb not null check ((jsonb_typeof(private_evidence)='object'
    and private_evidence->>'schema_version'='analysis.private-evidence.v1'
    and private_evidence->>'projection_of'=artifact_id || '@' || artifact_version::text) is true),
  safe_projection jsonb not null check ((jsonb_typeof(safe_projection)='object'
    and safe_projection->>'wire_kind'='watashi.map.v2'
    and safe_projection->>'projection_of'=artifact_id || '@' || artifact_version::text) is true),
  content_text text not null,
  generated_at timestamptz not null default clock_timestamp(),
  unique(user_id,report_type,report_mode,period_start,period_end,source_guard),
  check (octet_length(private_evidence::text)+octet_length(safe_projection::text)+octet_length(content_text)<=2097152)
);
create index analysis_observed_owner_history on public.analysis_observed_artifacts
  (user_id,report_type,generated_at desc,id);
alter table public.analysis_observed_artifacts enable row level security;
revoke all on public.analysis_observed_artifacts from public,anon,authenticated,service_role;
grant select,insert,delete on public.analysis_observed_artifacts to service_role;

create function public.analysis_observed_mode_allowed(p_tier text,p_mode text,p_history boolean)
returns boolean language sql immutable security invoker set search_path='' as $$
  select coalesce(p_mode in ('light','standard','deep') and
    (p_tier='premium' or (p_tier='plus' and p_mode in ('light','standard'))
      or (p_tier='free' and p_mode='light' and not p_history)),false);
$$;

-- A single statement snapshot, with a DB-native guard distinct from CMEE's
-- canonical-byte commitments. Sources leave this RPC only for server memory.
create function public.analysis_observed_source_snapshot(
  p_user_id uuid,p_start timestamptz,p_end timestamptz,p_mode text,p_report_type text)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare tier text; members jsonb; instant timestamptz := statement_timestamp();
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  tier := coalesce(tier,'free');
  if p_report_type not in ('latest','monthly') or p_start is null or p_end is null
    or p_start>=p_end or p_end>instant or not isfinite(p_start) or not isfinite(p_end) then
    raise sqlstate '22023' using message='analysis_period_invalid'; end if;
  if not public.analysis_observed_mode_allowed(tier,p_mode,p_report_type='monthly') then
    raise sqlstate '42501' using message='analysis_mode_unavailable'; end if;
  if not public.emlis_parent_visible(p_start at time zone 'UTC',tier,instant) then
    raise sqlstate 'P0002' using message='analysis_period_not_retained'; end if;
  select coalesce(jsonb_agg(jsonb_build_object('original',public.emlis_parent_source(e),
    'thread',case when t.id is null then null else to_jsonb(t) end,
    'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq)
      from public.emlis_thread_events v where v.thread_id=t.id),'[]'::jsonb))
    order by e.created_at,e.id),'[]'::jsonb) into members
  from (select * from public.emotions where user_id=p_user_id
    and created_at >= p_start at time zone 'UTC' and created_at < p_end at time zone 'UTC'
    order by created_at,id limit 101) e
  left join public.emlis_input_threads t on t.original_emotion_id=e.id;
  if jsonb_array_length(members)>100 then
    raise sqlstate '54000' using message='analysis_period_limit_exceeded'; end if;
  return jsonb_build_object('tier',tier,'now',instant,'members',members,'guard',
    'analysis-db-v1:' || encode(sha256(convert_to(jsonb_build_object(
      'owner',p_user_id,'start',p_start,'end',p_end,'mode',p_mode,
      'type',p_report_type,'tier',tier,'members',members)::text,'UTF8')),'hex'));
end;
$$;

-- Fail fast on contention; never hold a writer waiting while acquiring these
-- SHARE locks. They exclude phantoms as well as source edits for this short RPC.
-- The auth row lock comes first to avoid account-cascade/FK lock inversion.
create function public.analysis_observed_commit(
  p_user_id uuid,p_start timestamptz,p_end timestamptz,p_mode text,p_report_type text,
  p_guard text,p_artifact_id text,p_private_evidence jsonb,p_projection jsonb,p_text text)
returns uuid language plpgsql volatile security definer set search_path='' as $$
declare snap jsonb; rid uuid; existing uuid;
begin
  if current_setting('transaction_isolation') <> 'read committed' then
    raise sqlstate '40001' using message='analysis_isolation_unavailable'; end if;
  perform 1 from auth.users where id=p_user_id for key share nowait;
  if not found then raise sqlstate 'P0002' using message='analysis_owner_unavailable'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events
    in share mode nowait;
  snap := public.analysis_observed_source_snapshot(p_user_id,p_start,p_end,p_mode,p_report_type);
  if snap->>'guard' is distinct from p_guard then
    raise sqlstate '40001' using message='analysis_source_changed'; end if;
  if p_artifact_id !~ '^artifact:[0-9a-f]{32}$' or p_artifact_id is null then
    raise sqlstate '22023' using message='analysis_identity_invalid'; end if;
  rid := substring(p_artifact_id from 10)::uuid;
  -- Same frozen source and period resolves the original immutable identity.
  insert into public.analysis_observed_artifacts(id,artifact_id,artifact_version,user_id,
    report_type,report_mode,access_tier,period_start,period_end,source_guard,
    private_evidence,safe_projection,content_text)
  values(rid,p_artifact_id,1,p_user_id,p_report_type,p_mode,snap->>'tier',p_start,p_end,p_guard,
    p_private_evidence,p_projection,p_text)
  on conflict(user_id,report_type,report_mode,period_start,period_end,source_guard) do nothing;
  select id into existing from public.analysis_observed_artifacts where user_id=p_user_id
    and report_type=p_report_type and report_mode=p_mode and period_start=p_start and period_end=p_end
    and source_guard=p_guard;
  return existing;
exception when lock_not_available or deadlock_detected then
  raise sqlstate '40001' using message='analysis_source_busy';
end;
$$;

-- Closed public row envelope. No private JSON is returned by read endpoints.
create function public.analysis_observed_read(
  p_user_id uuid,p_report_type text default 'latest',p_mode text default null,
  p_id uuid default null,p_start timestamptz default null,p_end timestamptz default null,
  p_limit integer default 60,p_offset integer default 0,p_history boolean default false,p_days integer default null)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare tier text; r public.analysis_observed_artifacts; snap jsonb;
  items jsonb := '[]'; skipped integer := 0;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  tier := coalesce(tier,'free');
  if p_history and tier='free' then raise sqlstate '42501' using message='analysis_history_unavailable'; end if;
  if p_limit not between 1 and 200 or p_offset not between 0 and 10000
    or (p_days is not null and p_days not between 1 and 9999) then
    raise sqlstate '22023' using message='analysis_page_invalid'; end if;
  for r in select * from public.analysis_observed_artifacts a where a.user_id=p_user_id
    and (p_id is null or a.id=p_id) and (p_id is not null or a.report_type=p_report_type)
    and (p_mode is null or a.report_mode=p_mode)
    and (p_days is null or a.period_end-a.period_start=make_interval(days=>p_days))
    and (p_start is null or a.period_start=p_start) and (p_end is null or a.period_end=p_end)
    order by case when p_history then a.period_end end desc,a.generated_at desc,a.id desc loop
    if r.access_tier<>tier or not public.analysis_observed_mode_allowed(tier,r.report_mode,
      p_history or r.report_type='monthly') then continue; end if;
    begin
      snap := public.analysis_observed_source_snapshot(p_user_id,r.period_start,r.period_end,r.report_mode,r.report_type);
    exception when no_data_found or insufficient_privilege or program_limit_exceeded then continue;
    end;
    if snap->>'guard' is distinct from r.source_guard then continue; end if;
    if skipped<p_offset then skipped:=skipped+1; continue; end if;
    items := items || jsonb_build_array(jsonb_build_object('id',r.id,'report_type',r.report_type,
      'report_mode',r.report_mode,'title','わたしマップ','period_start',r.period_start,
      'period_end',r.period_end,'generated_at',r.generated_at,'updated_at',r.generated_at,
      'content_text',r.content_text,'content_json',jsonb_build_object('report_mode',r.report_mode,
        'watashiMap',r.safe_projection)));
    exit when jsonb_array_length(items)>=p_limit;
  end loop;
  return jsonb_build_object('subscription_tier',tier,'items',items,'matched',
    exists(select 1 from public.analysis_observed_artifacts where user_id=p_user_id and id=p_id));
end;
$$;

create function public.analysis_observed_immutable() returns trigger
language plpgsql security invoker set search_path='' as $$
begin raise sqlstate '55000' using message='analysis_artifact_immutable'; end;
$$;
create trigger analysis_observed_no_update before update on public.analysis_observed_artifacts
  for each row execute function public.analysis_observed_immutable();

-- Deletion, including cascading deletion, removes the complete private row.
-- New records also dirty overlapping latest windows. No source rows are edited.
create function public.analysis_observed_invalidate() returns trigger
language plpgsql security definer set search_path='' as $$
declare owner_id uuid; input_id uuid; ts timestamp; row_data jsonb;
begin
  if TG_OP='UPDATE' then
    if to_jsonb(OLD)=to_jsonb(NEW) then return null; end if;
    if TG_TABLE_NAME='profiles' and (to_jsonb(OLD)->>'subscription_tier') is not distinct from
      (to_jsonb(NEW)->>'subscription_tier') then return null; end if;
  end if;
  for row_data in select value from jsonb_array_elements(
    case when TG_OP='INSERT' then jsonb_build_array(to_jsonb(NEW))
         when TG_OP='DELETE' then jsonb_build_array(to_jsonb(OLD))
         else jsonb_build_array(to_jsonb(OLD),to_jsonb(NEW)) end) loop
    if TG_TABLE_NAME='emotions' then
      owner_id := (row_data->>'user_id')::uuid; ts := (row_data->>'created_at')::timestamp;
    elsif TG_TABLE_NAME='profiles' then
      delete from public.analysis_observed_artifacts where user_id=(row_data->>'id')::uuid;
      continue;
    else
      if TG_TABLE_NAME='emlis_input_threads' then
        input_id := (row_data->>'original_emotion_id')::uuid;
        owner_id := (row_data->>'user_id')::uuid;
      else
        select original_emotion_id,user_id into input_id,owner_id from public.emlis_input_threads
          where id=(row_data->>'thread_id')::uuid;
      end if;
      select created_at into ts from public.emotions where id=input_id;
      -- Parent/thread cascade triggers cover deleted lookup targets.
    end if;
    delete from public.analysis_observed_artifacts where user_id=owner_id
      and ((ts at time zone 'UTC' >= period_start and ts at time zone 'UTC' < period_end)
        or (TG_TABLE_NAME='emotions' and report_type='latest'));
  end loop;
  return null;
end;
$$;
create trigger analysis_emotions_changed after insert or update or delete on public.emotions
  for each row execute function public.analysis_observed_invalidate();
create trigger analysis_threads_changed after insert or update or delete on public.emlis_input_threads
  for each row execute function public.analysis_observed_invalidate();
create trigger analysis_events_changed after insert or update or delete on public.emlis_thread_events
  for each row execute function public.analysis_observed_invalidate();
create trigger analysis_tier_changed after update of subscription_tier or delete on public.profiles
  for each row execute function public.analysis_observed_invalidate();

revoke all on function public.analysis_observed_mode_allowed(text,text,boolean),
  public.analysis_observed_source_snapshot(uuid,timestamptz,timestamptz,text,text),
  public.analysis_observed_commit(uuid,timestamptz,timestamptz,text,text,text,text,jsonb,jsonb,text),
  public.analysis_observed_read(uuid,text,text,uuid,timestamptz,timestamptz,integer,integer,boolean,integer),
  public.analysis_observed_immutable(),public.analysis_observed_invalidate() from public,anon,authenticated,service_role;
grant execute on function public.analysis_observed_mode_allowed(text,text,boolean),
  public.analysis_observed_source_snapshot(uuid,timestamptz,timestamptz,text,text),
  public.analysis_observed_commit(uuid,timestamptz,timestamptz,text,text,text,text,jsonb,jsonb,text),
  public.analysis_observed_read(uuid,text,text,uuid,timestamptz,timestamptz,integer,integer,boolean,integer) to service_role;
commit;
