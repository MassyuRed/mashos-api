-- Hide the previous writer's explicitly declined analysis on every saved read.
-- Older maps without plan-generation provenance keep their existing checks.
begin;

create function public.analysis_cumulative_has_accepted_reading(p_projection jsonb,p_evidence jsonb)
returns boolean language sql immutable security invoker set search_path='' as $$
  select case
    when p_projection->>'wire_kind'='watashi.map.v3' then
      not coalesce(p_projection#>'{overview,primary_structures}'='[]'::jsonb,false)
      and not (p_projection#>'{overview,primary_structures}' is null
        and coalesce(p_evidence#>'{graph,meaning_review,node_local_plan,plan,overview,primary_structures}'='[]'::jsonb,false))
    else true end;
$$;
revoke all on function public.analysis_cumulative_has_accepted_reading(jsonb,jsonb)
  from public,anon,authenticated,service_role;
grant execute on function public.analysis_cumulative_has_accepted_reading(jsonb,jsonb) to service_role;

create or replace function public.analysis_cumulative_current_id(p_user_id uuid,p_guard text)
returns uuid language sql stable security invoker set search_path='' as $$
  select a.id from public.analysis_observed_artifacts a
  where a.user_id=p_user_id and a.source_profile='cumulative.v1'
    and (a.source_guard=p_guard or a.cumulative_source_guard=p_guard)
    and public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence)
  order by a.generated_at desc,a.id desc limit 1;
$$;

create or replace function public.analysis_cumulative_commit(p_user_id uuid,p_guard text,
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
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events,
    public.deep_insight_questions,public.analysis_map_interpretation_corrections
    in share mode nowait;
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  if snap->>'guard' is distinct from p_guard then
    raise sqlstate '40001' using message='analysis_source_changed'; end if;
  if p_artifact_id is not null and not public.analysis_cumulative_has_accepted_reading(p_projection,p_private_evidence) then
    raise sqlstate '22023' using message='analysis_primary_structure_unavailable'; end if;
  rid:=public.analysis_cumulative_current_id(p_user_id,p_guard);
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
  insert into public.analysis_cumulative_months as month(user_id,snapshot_month,artifact_id)
    values(p_user_id,month_key,rid) on conflict(user_id,snapshot_month) do update
    set artifact_id=excluded.artifact_id,captured_at=excluded.captured_at
    where exists(select 1 from public.analysis_observed_artifacts previous
      where previous.id=month.artifact_id and previous.user_id=p_user_id
        and not public.analysis_cumulative_has_accepted_reading(previous.safe_projection,previous.private_evidence));
  -- Keep ordinary pruning for superseded current caches and retain the
  -- explicitly withheld records for provenance without serving them.
  delete from public.analysis_observed_artifacts a where a.user_id=p_user_id
    and a.source_profile='cumulative.v1' and a.id<>rid
    and public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence)
    and not exists(select 1 from public.analysis_cumulative_months m where m.artifact_id=a.id);
  return rid;
exception when lock_not_available or deadlock_detected then
  raise sqlstate '40001' using message='analysis_source_busy';
end;
$$;

create or replace function public.analysis_cumulative_read(p_user_id uuid,p_id uuid default null,
  p_history boolean default false,p_limit integer default 60,p_offset integer default 0,
  p_month date default null,p_metadata_only boolean default false)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; tier text; max_months integer; current_id uuid; items jsonb; withheld boolean:=false;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  if not found or tier not in ('free','plus','premium') then
    raise sqlstate '42501' using message='analysis_owner_unavailable'; end if;
  max_months:=case tier when 'free' then 2 when 'plus' then 12 else null end;
  if p_limit not between 1 and 200 or p_offset not between 0 and 10000 then
    raise sqlstate '22023' using message='analysis_page_invalid'; end if;
  if not p_history and p_month is null then
    snap:=public.analysis_cumulative_source_snapshot(p_user_id);
    current_id:=public.analysis_cumulative_current_id(p_user_id,snap->>'guard');
    if current_id is null and p_id is null then
      select exists(select 1 from public.analysis_observed_artifacts a
        where a.user_id=p_user_id and a.source_profile='cumulative.v1'
          and (a.source_guard=snap->>'guard' or a.cumulative_source_guard=snap->>'guard')
          and not public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence))
      into withheld;
    end if;
  elsif p_history and p_month is not null and p_id is null then
    select exists(select 1 from public.analysis_cumulative_months m
      join public.analysis_observed_artifacts a on a.id=m.artifact_id and a.user_id=m.user_id
      where m.user_id=p_user_id and m.snapshot_month=p_month
        and not public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence))
    into withheld;
  end if;
  with ranked as (
    select m.*,row_number() over(order by snapshot_month desc) as n
    from public.analysis_cumulative_months m
      join public.analysis_observed_artifacts a on a.id=m.artifact_id and a.user_id=m.user_id
    where m.user_id=p_user_id
      and public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence)
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
      'map_context',private_evidence->'coverage') ||
      case when tier='premium' and safe_projection->>'wire_kind'='watashi.map.v3'
          and private_evidence->>'projection_of'=safe_projection->>'projection_of'
          and jsonb_typeof(private_evidence #> '{graph,meaning_review,structure_relations,views}')='array'
        then jsonb_build_object('structure_relations',
          private_evidence #> '{graph,meaning_review,structure_relations,views}')
        else '{}'::jsonb end) end
    order by snapshot_month desc nulls last,generated_at desc,id desc),'[]'::jsonb) into items from page;
  return jsonb_build_object('items',items,'subscription_tier',tier,'matched',
    exists(select 1 from public.analysis_observed_artifacts where user_id=p_user_id
      and source_profile='cumulative.v1' and id=p_id),'history_limit',max_months)
      || case when withheld then '{"withheld":true}'::jsonb else '{}'::jsonb end;
end;
$$;

create or replace function public.analysis_if_base_context(p_user_id uuid,p_base_ref text)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; parent public.analysis_observed_artifacts; refs jsonb;
begin
  perform public.analysis_if_require_premium(p_user_id);
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select * into parent from public.analysis_observed_artifacts where user_id=p_user_id
    and artifact_id || '@' || artifact_version::text=p_base_ref and source_profile='cumulative.v1'
    and (source_guard=snap->>'guard' or cumulative_source_guard=snap->>'guard')
    and public.analysis_cumulative_has_accepted_reading(safe_projection,private_evidence);
  if not found then raise sqlstate 'P0002' using message='analysis_if_base_unavailable'; end if;
  select coalesce(jsonb_agg(m#>>'{original,id}' order by ord),'[]'::jsonb) into refs
    from jsonb_array_elements(snap->'members') with ordinality as x(m,ord);
  if jsonb_array_length(refs)=0 then raise sqlstate 'P0002' using message='analysis_if_base_unavailable'; end if;
  return jsonb_build_object('base_observed_map_ref',p_base_ref,'base_source_guard',snap->>'guard',
    'base_projection',parent.safe_projection,'base_private_evidence',parent.private_evidence,
    'source_record_refs',refs,'subscription_tier',snap->>'tier');
end;
$$;

commit;
