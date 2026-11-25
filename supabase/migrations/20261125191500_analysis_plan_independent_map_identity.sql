-- Current maps bind the owner's saved material independently of the viewer's
-- history window. The paid Emlis transport stays available for its own
-- admission check while the Map source digest excludes the transport envelope.
begin;

alter table public.analysis_observed_artifacts
  add column cumulative_source_guard text
    check (cumulative_source_guard ~ '^analysis-db-cumulative-v1:[0-9a-f]{64}$');
alter table public.analysis_map_interpretation_corrections
  add column cumulative_cohort jsonb
    check (jsonb_typeof(cumulative_cohort)='array');

-- Preserve only legacy guards that the unchanged owner can still reproduce.
-- The temporary originals are discarded with the transaction.
create temporary table legacy_current_map_material on commit drop as
select o.user_id, public.analysis_cumulative_source_snapshot(o.user_id) as snapshot
from (
  select user_id from public.analysis_observed_artifacts where source_profile='cumulative.v1'
  union
  select user_id from public.analysis_map_interpretation_corrections
) o
join public.profiles p on p.id=o.user_id
where coalesce(p.subscription_tier,'free') in ('free','plus','premium');

create function public.analysis_cumulative_member_source(p_member jsonb)
returns jsonb language sql immutable strict security invoker set search_path='' as $$
  select (p_member - 'context') #- '{thread,revision}';
$$;

create function public.analysis_cumulative_member_guard(p_member jsonb)
returns text language sql immutable strict security invoker set search_path='' as $$
  select 'analysis-map-member-v1:' || encode(sha256(convert_to(
    public.analysis_cumulative_member_source(p_member)::text,'UTF8')),'hex');
$$;

alter table public.analysis_map_interpretation_corrections
  disable trigger analysis_map_correction_no_update;
update public.analysis_map_interpretation_corrections c set cumulative_cohort=(
  select jsonb_agg(jsonb_build_object('record_ref',m#>>'{original,id}',
    'source_guard',public.analysis_cumulative_member_guard(m)) order by m#>>'{original,id}')
  from jsonb_array_elements(prior.snapshot->'members') m
  where exists (select 1 from jsonb_array_elements(c.target_context->'cohort') dependency
    where dependency->>'record_ref'=m#>>'{original,id}')
)
from pg_temp.legacy_current_map_material prior
where c.user_id=prior.user_id
  and exists(select 1 from jsonb_array_elements(coalesce(prior.snapshot->'map_corrections','[]'::jsonb)) saved
    where saved->>'correction_id'=c.id::text and saved->>'source_state'='ACTIVE');
alter table public.analysis_map_interpretation_corrections
  enable trigger analysis_map_correction_no_update;

create or replace function public.analysis_map_correction_sources(p_user_id uuid,p_members jsonb)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare result jsonb;
begin
  if jsonb_typeof(p_members) is distinct from 'array' then
    raise sqlstate '22023' using message='analysis_map_correction_members_invalid';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'schema_version','cocolon.analysis.map_correction.v1',
    'correction_id',c.id,'owner_scope',c.user_id,'recorded_at',c.recorded_at,
    'target_context',c.target_context,
    'explanation',jsonb_build_object('source_role','USER_ANALYSIS_MAP_CORRECTION','text',c.explanation),
    'source_state',case when not exists (
      select 1 from jsonb_array_elements(coalesce(c.cumulative_cohort,c.target_context->'cohort')) dependency
      where (select count(*) from jsonb_array_elements(p_members) member
        where member#>>'{original,id}' = dependency->>'record_ref'
          and (public.analysis_cumulative_member_guard(member)=dependency->>'source_guard'
            or (c.cumulative_cohort is null and 'analysis-map-member-v1:' || encode(sha256(convert_to(
              (member #- '{thread,revision}' #- '{context,now}')::text,'UTF8')),'hex')
                = dependency->>'source_guard'))) <> 1
      ) then 'ACTIVE' else 'STALE' end) order by c.recorded_at,c.id),'[]'::jsonb)
    into result from public.analysis_map_interpretation_corrections c
    where c.user_id=p_user_id;
  return result;
end;
$$;

create function public.analysis_cumulative_material_guard(p_user_id uuid,p_snapshot jsonb)
returns text language plpgsql immutable strict security invoker set search_path='' as $$
declare members jsonb; sources jsonb;
begin
  select coalesce(jsonb_agg(public.analysis_cumulative_member_source(m) order by ord),'[]'::jsonb)
    into members from jsonb_array_elements(p_snapshot->'members') with ordinality as x(m,ord);
  sources:=jsonb_build_object('owner',p_user_id,'members',members);
  if p_snapshot ? 'map_corrections' then
    sources:=sources || jsonb_build_object('map_corrections',p_snapshot->'map_corrections');
  end if;
  return 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(sources::text,'UTF8')),'hex');
end;
$$;

alter function public.analysis_cumulative_source_snapshot(uuid)
  rename to analysis_cumulative_snapshot_with_handoff;

create function public.analysis_cumulative_source_snapshot(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  select snapshot || jsonb_build_object('guard',public.analysis_cumulative_material_guard(p_user_id,snapshot))
  from public.analysis_cumulative_snapshot_with_handoff(p_user_id) snapshot;
$$;

revoke all on function public.analysis_cumulative_source_snapshot(uuid) from public,anon,authenticated;
grant execute on function public.analysis_cumulative_source_snapshot(uuid) to service_role;

-- Only currently reproducible versions gain a stable alias. Existing
-- projections, guard receipts, published monthly IDs and text stay intact.
alter table public.analysis_observed_artifacts disable trigger analysis_observed_no_update;
with normalized as materialized (
  select user_id,snapshot->>'guard' as previous_guard,
    public.analysis_cumulative_material_guard(user_id,snapshot) as current_guard
  from pg_temp.legacy_current_map_material
)
update public.analysis_observed_artifacts a
set cumulative_source_guard=n.current_guard
from normalized n
where a.user_id=n.user_id and a.source_profile='cumulative.v1'
  and a.source_guard=n.previous_guard and a.source_guard<>n.current_guard;
alter table public.analysis_observed_artifacts enable trigger analysis_observed_no_update;

create index analysis_cumulative_guard_alias on public.analysis_observed_artifacts(user_id,cumulative_source_guard)
  where cumulative_source_guard is not null;

create function public.analysis_cumulative_current_id(p_user_id uuid,p_guard text)
returns uuid language sql stable security invoker set search_path='' as $$
  select a.id from public.analysis_observed_artifacts a
  where a.user_id=p_user_id and a.source_profile='cumulative.v1'
    and (a.source_guard=p_guard or a.cumulative_source_guard=p_guard)
  order by a.generated_at desc,a.id desc limit 1;
$$;

revoke all on function public.analysis_cumulative_member_source(jsonb),
  public.analysis_cumulative_member_guard(jsonb),
  public.analysis_cumulative_material_guard(uuid,jsonb),
  public.analysis_cumulative_current_id(uuid,text) from public,anon,authenticated,service_role;
grant execute on function public.analysis_cumulative_member_source(jsonb),
  public.analysis_cumulative_member_guard(jsonb),
  public.analysis_cumulative_material_guard(uuid,jsonb),
  public.analysis_cumulative_current_id(uuid,text) to service_role;

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

create or replace function public.analysis_cumulative_read(p_user_id uuid,p_id uuid default null,
  p_history boolean default false,p_limit integer default 60,p_offset integer default 0,
  p_month date default null,p_metadata_only boolean default false)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
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
    current_id:=public.analysis_cumulative_current_id(p_user_id,snap->>'guard');
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

create or replace function public.analysis_map_correction_submit_original_field(
  p_user_id uuid,p_artifact_ref text,p_kind text,p_ref text,p_field text,
  p_target_text text,p_explanation text,p_idempotency_key text)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare old public.analysis_map_interpretation_corrections; artifact public.analysis_observed_artifacts;
  body jsonb; snap jsonb; visible jsonb; selected jsonb; field_text text; first_pos integer;
  node_refs text[]; record_refs text[]; cohort jsonb; target jsonb; rid uuid; array_parts text[];
begin
  if current_setting('transaction_isolation') <> 'read committed' then
    raise sqlstate '40001' using message='analysis_isolation_unavailable';
  end if;
  if p_artifact_ref is null or p_artifact_ref !~ '^artifact:[0-9a-f]{32}@1$'
    or p_kind is null or p_kind not in ('overview','node','edge')
    or p_ref is null or p_field is null
    or p_target_text is null or char_length(p_target_text) not between 1 and 2000 or btrim(p_target_text)=''
    or p_explanation is null or char_length(p_explanation) not between 1 and 2000 or btrim(p_explanation)=''
    or p_idempotency_key is null or char_length(p_idempotency_key) not between 1 and 128 or btrim(p_idempotency_key)='' then
    raise sqlstate '22023' using message='analysis_map_correction_invalid';
  end if;
  body:=jsonb_build_object('artifact_ref',p_artifact_ref,'kind',p_kind,'ref',p_ref,
    'field',p_field,'target_text',p_target_text,'explanation',p_explanation);
  -- The same owner lock/order as cumulative commits. A repeated command is
  -- resolved before target lookup, even after its old current cache is gone.
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002' using message='analysis_owner_unavailable'; end if;
  select * into old from public.analysis_map_interpretation_corrections
    where user_id=p_user_id and idempotency_key=p_idempotency_key;
  if found then
    if old.request_body is distinct from body then
      raise sqlstate '23505' using message='analysis_map_correction_idempotency_conflict';
    end if;
    return public.analysis_map_correction_read(p_user_id,p_idempotency_key);
  end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events,
    public.analysis_observed_artifacts in share mode nowait;
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select * into artifact from public.analysis_observed_artifacts
    where user_id=p_user_id and artifact_id || '@' || artifact_version::text=p_artifact_ref
      and source_profile='cumulative.v1';
  if not found then raise sqlstate 'P0002' using message='analysis_map_correction_target_unavailable'; end if;
  if artifact.source_guard is distinct from snap->>'guard'
    and artifact.cumulative_source_guard is distinct from snap->>'guard' then
    raise sqlstate '40001' using message='analysis_map_correction_source_changed';
  end if;
  visible:=public.analysis_cumulative_read(p_user_id,artifact.id,false,200,0,null,false);
  if not exists(select 1 from jsonb_array_elements(visible->'items') row
      where row->>'id'=artifact.id::text) then
    raise sqlstate '42501' using message='analysis_map_correction_target_unavailable';
  end if;
  if artifact.safe_projection->>'wire_kind' is distinct from 'watashi.map.v3'
    or artifact.safe_projection->>'projection_of' is distinct from p_artifact_ref then
    raise sqlstate '22023' using message='analysis_map_correction_target_invalid';
  end if;
  if p_kind='overview' and p_ref='overview' and p_field in ('title','summary') then
    selected:=artifact.safe_projection->'overview';
    select array_agg(distinct row->>'saved_record_ref' order by row->>'saved_record_ref') into record_refs
      from jsonb_array_elements(artifact.private_evidence->'source_members') row;
  elsif p_kind='node' and p_ref ~ '^n[1-9][0-9]*$'
    and (p_field in ('title','summary','explanation') or p_field ~ '^(context|unknowns)\.(0|[1-9][0-9]{0,5})$') then
    select row into selected from jsonb_array_elements(artifact.safe_projection->'nodes') row
      where row->>'node_ref'=p_ref;
    node_refs:=array[p_ref];
  elsif p_kind='edge' and p_ref ~ '^e[1-9][0-9]*$' and p_field in ('label','explanation') then
    select row into selected from jsonb_array_elements(artifact.safe_projection->'edges') row
      where row->>'edge_ref'=p_ref;
    node_refs:=array[selected->>'from_ref',selected->>'to_ref'];
  else
    raise sqlstate '22023' using message='analysis_map_correction_target_invalid';
  end if;
  if selected is null then raise sqlstate '22023' using message='analysis_map_correction_target_invalid'; end if;
  if p_field ~ '^(context|unknowns)\.' then
    array_parts:=string_to_array(p_field,'.');
    if jsonb_typeof(selected->array_parts[1]->(array_parts[2]::integer)) is distinct from 'string' then
      raise sqlstate '22023' using message='analysis_map_correction_target_invalid';
    end if;
    field_text:=selected->array_parts[1]->>(array_parts[2]::integer);
  else
    if jsonb_typeof(selected->p_field) is distinct from 'string' then
      raise sqlstate '22023' using message='analysis_map_correction_target_invalid';
    end if;
    field_text:=selected->>p_field;
  end if;
  first_pos:=strpos(field_text,p_target_text);
  if first_pos=0 or strpos(substr(field_text,first_pos+1),p_target_text)>0 then
    raise sqlstate '22023' using message='analysis_map_correction_target_not_unique';
  end if;
  if node_refs is not null then
    select array_agg(distinct ref order by ref) into record_refs
      from jsonb_array_elements(artifact.private_evidence->'graph'->'nodes') node,
        jsonb_array_elements_text(node->'record_refs') ref
      where node->>'node_ref'=any(node_refs);
    if (select count(*) from jsonb_array_elements(artifact.private_evidence->'graph'->'nodes') node
          where node->>'node_ref'=any(node_refs)) <> cardinality(node_refs) then
      raise sqlstate '22023' using message='analysis_map_correction_cohort_invalid';
    end if;
  end if;
  if coalesce(cardinality(record_refs),0)=0 then
    raise sqlstate '22023' using message='analysis_map_correction_cohort_invalid';
  end if;
  select jsonb_agg(jsonb_build_object('record_ref',member#>>'{original,id}',
      'source_guard',public.analysis_cumulative_member_guard(member))
      order by member#>>'{original,id}') into cohort
    from jsonb_array_elements(snap->'members') member
    where member#>>'{original,id}'=any(record_refs);
  if jsonb_array_length(cohort) is distinct from cardinality(record_refs) then
    raise sqlstate '40001' using message='analysis_map_correction_source_changed';
  end if;
  target:=jsonb_build_object('artifact_ref',p_artifact_ref,'kind',p_kind,'ref',p_ref,
    'field',p_field,'target_text',p_target_text,'field_text',field_text,
    'source_guard',artifact.source_guard,'cohort',cohort);
  insert into public.analysis_map_interpretation_corrections
    (user_id,idempotency_key,request_body,target_context,explanation)
    values(p_user_id,p_idempotency_key,body,target,p_explanation) returning id into rid;
  return public.analysis_map_correction_read(p_user_id,p_idempotency_key);
end;
$$;

create or replace function public.analysis_if_sources_current(p_user_id uuid,p_guard text,p_refs jsonb)
returns boolean language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; raw_members jsonb; members jsonb; identity_body jsonb; legacy_identity jsonb;
  corrections jsonb; prefix jsonb:='[]'::jsonb; correction jsonb;
begin
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select coalesce(jsonb_agg(m order by ord),'[]'::jsonb),
    coalesce(jsonb_agg(m #- '{thread,revision}' #- '{context,now}' order by ord),'[]'::jsonb)
    into raw_members,members
    from jsonb_array_elements(snap->'members') with ordinality as x(m,ord)
    where p_refs ? (m#>>'{original,id}');
  if jsonb_array_length(members)<>jsonb_array_length(p_refs) then return false; end if;
  legacy_identity:=jsonb_build_object('owner',p_user_id,'members',members);
  select coalesce(jsonb_agg(public.analysis_cumulative_member_source(m) order by ord),'[]'::jsonb)
    into members from jsonb_array_elements(raw_members) with ordinality as x(m,ord);
  identity_body:=jsonb_build_object('owner',p_user_id,'members',members);
  if 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(identity_body::text,'UTF8')),'hex')=p_guard
    or 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(legacy_identity::text,'UTF8')),'hex')=p_guard then
    return true; end if;
  corrections:=public.analysis_map_correction_sources(p_user_id,raw_members);
  for correction in select value from jsonb_array_elements(corrections) loop
    prefix:=prefix || jsonb_build_array(correction);
    if 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      (identity_body || jsonb_build_object('map_corrections',prefix))::text,'UTF8')),'hex')=p_guard
      or 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      (legacy_identity || jsonb_build_object('map_corrections',prefix))::text,'UTF8')),'hex')=p_guard then
      return true; end if;
  end loop;
  return false;
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
    and (source_guard=snap->>'guard' or cumulative_source_guard=snap->>'guard');
  if not found then raise sqlstate 'P0002' using message='analysis_if_base_unavailable'; end if;
  select coalesce(jsonb_agg(m#>>'{original,id}' order by ord),'[]'::jsonb) into refs
    from jsonb_array_elements(snap->'members') with ordinality as x(m,ord);
  if jsonb_array_length(refs)=0 then raise sqlstate 'P0002' using message='analysis_if_base_unavailable'; end if;
  return jsonb_build_object('base_observed_map_ref',p_base_ref,'base_source_guard',snap->>'guard',
    'base_projection',parent.safe_projection,'base_private_evidence',parent.private_evidence,
    'source_record_refs',refs,'subscription_tier',snap->>'tier');
end;
$$;

create or replace function public.deep_insight_material(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  with profile as (
    select coalesce((select subscription_tier from public.profiles where id=p_user_id),'free') as tier,
      exists(select 1 from public.profiles where id=p_user_id
        and coalesce(subscription_tier,'free') in ('free','plus','premium')) as available
  ), records as (
    select e.id,e.created_at,record_fields.thought,record_fields.action,
      encode(sha256(convert_to(binding.original::text,'UTF8')),'hex') as source_version,
      pending.prompt as emlis_open_question,pending.question_id as emlis_open_question_id,
      coalesce(answers.items,'[]'::jsonb) as emlis_answered_questions,
      corrections.items as emlis_corrections,
      skipped.prompt as emlis_skipped_question
    from public.emotions e cross join profile
    left join public.emlis_input_threads t on t.original_emotion_id=e.id and t.user_id=e.user_id
    cross join lateral (select public.emlis_parent_source(e) as original,
      t.data->'analysis_material' as material) binding
    left join lateral (
      select count(*) filter (where v.kind='ANSWER') as answer_count,
        count(*) filter (where v.kind='OPERATION') as correction_count,
        max(v.seq) as last_source_update
      from public.emlis_thread_events v
      where v.thread_id=t.id and t.source_snapshot=binding.original
        and (v.kind='ANSWER' or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'))
    ) history on true
    left join lateral (
      -- A complete verbatim field keeps the existing receipt coordinates.
      -- A split or unassessed field stays out until its active ranges can be
      -- represented without joining separated passages.
      select binding.material->'active_fields' as fields, binding.material->>'record_version' as version,
        v.seq as observation_seq
      from public.emlis_thread_events v
      where history.last_source_update is not null
        and (history.answer_count>1 or history.correction_count>0)
        and v.id=t.last_observation_event_id and v.thread_id=t.id and v.kind='OBSERVATION'
        and v.seq>history.last_source_update
        and coalesce(t.data->>'evaluated_tier',profile.tier)=profile.tier
        and t.data->>'natural_meaning_profile'='source_grounded_active_meaning.v1'
        and v.payload#>>'{artifact,meaning_profile}'=t.data->>'natural_meaning_profile'
        and v.payload#>'{artifact,analysis_material}'=binding.material
        and binding.material->>'schema_version'='cocolon.cmee.emlis_analysis_material.v1'
        and binding.material->>'owner_scope'=p_user_id::text
        and binding.material->>'record_ref'=e.id::text
        and binding.material->'original_record'=binding.original
        and v.payload->>'source_prefix_ref'=t.source_prefix_ref
        and binding.material->>'source_prefix_ref'=t.source_prefix_ref
        and binding.material#>>'{coverage,active_state}'='RESOLVED'
        and jsonb_typeof(binding.material->'active_fields')='array'
    ) active on true
    left join lateral (
      select max(f->>'text') filter (where f->>'field_path'='memo'
          and f->>'text'=e.memo and f->>'scalar_end'=char_length(e.memo)::text) as thought,
        max(f->>'text') filter (where f->>'field_path'='memo_action'
          and f->>'text'=e.memo_action and f->>'scalar_end'=char_length(e.memo_action)::text) as action
      from jsonb_array_elements(coalesce(active.fields,'[]'::jsonb)) f
      where f->>'source_role'='ORIGINAL_INPUT' and f->>'source_id'=e.id::text
        and f->>'record_ref'=e.id::text and f->>'record_version'=active.version
        and f->>'scalar_start'='0'
    ) active_original on true
    cross join lateral (
      select case when history.correction_count=0 and history.answer_count<2
        then e.memo else active_original.thought end as thought,
        case when history.correction_count=0 and history.answer_count<2
        then e.memo_action else active_original.action end as action
    ) record_fields
    left join lateral (
      select q.question_id,q.payload->>'prompt_private' as prompt
      from public.emlis_thread_events q
      where t.state='AWAITING_ANSWER' and t.source_snapshot=public.emlis_parent_source(e)
        and coalesce(t.data->>'evaluated_tier',profile.tier)=profile.tier
        and q.thread_id=t.id and q.kind='QUESTION' and q.round_index=t.issued_count
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=q.thread_id
          and v.seq>q.seq and (v.kind='TERMINAL' or v.kind='ANSWER' or
            (v.kind='OPERATION' and (v.payload ? 'question_ending' or
              v.payload->>'stage'='INTERPRETATION_CORRECTION'))))
      order by q.seq desc limit 1
    ) pending on true
    left join lateral (
      select jsonb_agg((jsonb_build_object('id',a.id,'question_id',q.question_id,'answered_at',a.recorded_at,
        'source_version',encode(sha256(convert_to((a.payload->'source')::text,'UTF8')),'hex'),
        'question',case when history.correction_count=0 then q.payload->>'prompt_private' end,
        'answer',a.payload#>>'{source,answer_text_private}')
        || case when history.correction_count>0
          -- Its earlier wording may still prevent a repeat, but the admitted
          -- answer no longer certifies all of the earlier question's premises.
          then jsonb_build_object('previous_question',q.payload->>'prompt_private')
          else '{}'::jsonb end)
        order by q.seq) as items
      from public.emlis_thread_events q join public.emlis_thread_events a
        on a.thread_id=q.thread_id and a.question_id=q.question_id and a.kind='ANSWER'
        and a.round_index=q.round_index and a.seq>q.seq
      where q.thread_id=t.id and q.kind='QUESTION' and t.source_snapshot=public.emlis_parent_source(e)
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and a.payload#>>'{source,answer_id}'=a.id::text
        and a.payload#>>'{source,thread_id}'=t.id::text
        and a.payload#>>'{source,question_id}'=q.question_id
        and a.payload#>>'{source,round_index}'=a.round_index::text
        and a.payload#>>'{source,original_source_ref}'=t.data->>'original_source_ref'
        and a.payload#>>'{source,source_role}'='SUPPLEMENTAL_ANSWER'
        and a.payload#>>'{source,source_version}'='cocolon.cmee.supplemental_answer.v1'
        and a.payload#>>'{source,answer_text_private}' ~ '[^[:space:]]'
        and (history.answer_count=1 and history.correction_count=0 or exists (
          select 1 from jsonb_array_elements(coalesce(active.fields,'[]'::jsonb)) f
          where f->>'source_role'='SUPPLEMENTAL_ANSWER' and f->>'source_id'=a.id::text
            and f->>'record_ref'=e.id::text and f->>'record_version'=active.version
            and f->>'field_path'='memo' and f->>'scalar_start'='0'
            and f->>'text'=a.payload#>>'{source,answer_text_private}'
            and f->>'scalar_end'=char_length(a.payload#>>'{source,answer_text_private}')::text))
    ) answers on true
    left join lateral (
      -- Use the replacement range that CMEE kept. The whole explanation can
      -- include the superseded wording and is never sent to the question model.
      select jsonb_agg(jsonb_build_object('id',c.id,'recorded_at',c.recorded_at,
        'text',f->>'text','scalar_start',span.start_at,'source_version',
        encode(sha256(convert_to(jsonb_build_array(c.payload->'source',t.source_prefix_ref,
          span.start_at,span.end_at)::text,'UTF8')),'hex'))
        order by c.seq) as items
      from jsonb_array_elements(coalesce(active.fields,'[]'::jsonb)) f
      join public.emlis_thread_events c on c.id::text=f->>'source_id' and c.thread_id=t.id
      cross join lateral (select c.payload->'source' as proof) correction
      cross join lateral (
        select case when f->>'scalar_start' ~ '^(0|[1-9][0-9]{0,3})$'
          then (f->>'scalar_start')::integer end as start_at,
          case when f->>'scalar_end' ~ '^[1-9][0-9]{0,3}$'
          then (f->>'scalar_end')::integer end as end_at
      ) span
      where f->>'source_role'='USER_INTERPRETATION_CORRECTION'
        and f->>'record_ref'=e.id::text and f->>'record_version'=active.version
        and f->>'field_path'='memo' and f->>'text' ~ '[^[:space:]]'
        and c.kind='OPERATION' and c.payload->>'stage'='INTERPRETATION_CORRECTION'
        and c.payload->>'status'='SAVED' and c.payload->>'assessment'='UNASSESSED'
        and c.idempotency_key is not null
        and c.payload->>'request_fingerprint' ~ '^interpretation-correction-request-[0-9a-f]{64}$'
        and correction.proof->>'source_role'=f->>'source_role'
        and correction.proof->>'correction_id'=c.id::text
        and correction.proof->>'thread_id'=t.id::text
        and correction.proof->>'original_source_ref'=t.data->>'original_source_ref'
        and span.start_at<span.end_at and span.end_at<=char_length(correction.proof->>'explanation')
        and f->>'text'=substr(correction.proof->>'explanation',span.start_at+1,
          greatest(0,span.end_at-span.start_at))
        and f#>>'{evidence,field_sha256}'=encode(sha256(convert_to(correction.proof->>'explanation','UTF8')),'hex')
        and f#>>'{evidence,literal_sha256}'=encode(sha256(convert_to(f->>'text','UTF8')),'hex')
        and binding.material#>'{graph,source_updates}' @> jsonb_build_array(jsonb_build_object(
          'operation','REVISE','record_ref',e.id,'replacement_evidence_refs',
          jsonb_build_array(jsonb_build_object('source_envelope_id',f->>'source_envelope_id'))))
        and exists (select 1 from public.emlis_thread_events target
          where target.id::text=correction.proof->>'target_event_id' and target.thread_id=t.id
            and target.kind='OBSERVATION' and target.seq<c.seq
            and strpos(target.payload->>'text',correction.proof->>'target_text')>0)
        and exists (select 1 from public.emlis_thread_events v
          where v.thread_id=t.id and v.kind='OBSERVATION' and v.payload->>'stage'='CORRECTED'
            and v.operation_id=c.operation_id and c.seq<v.seq and v.seq<=active.observation_seq)
    ) corrections on true
    left join lateral (
      select q.payload->>'prompt_private' as prompt
      from public.emlis_thread_events q
      where profile.tier='premium' and q.thread_id=t.id and q.kind='QUESTION'
        and q.round_index=t.issued_count and t.source_snapshot=public.emlis_parent_source(e)
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and exists (
          select 1 from public.emlis_thread_events v
          where v.thread_id=q.thread_id and v.round_index=q.round_index and v.seq>q.seq
            -- These older action events use the unique question in their round
            -- without copying its ID. An explicit ID, when present, must match.
            and (v.question_id is null or v.question_id=q.question_id)
            and v.idempotency_key is not null and v.payload->>'request_fingerprint' ~ '^action-request-[0-9a-f]{64}$'
            and ((v.kind='TERMINAL' and v.payload->>'reason' in ('skip','stop'))
              or (v.kind='OPERATION' and v.payload->>'stage'='NATURAL_FINAL_REQUESTED'
                and v.payload->>'status'='RUNNING' and v.payload->>'question_ending' in ('skip','stop')))
        )
        -- A stop after an answer closes the thread, not a pending question.
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=q.thread_id and v.seq>q.seq
          and ((v.kind='ANSWER' and v.question_id=q.question_id and v.round_index=q.round_index)
            or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')))
      order by q.seq desc limit 1
    ) skipped on true
    where e.user_id=p_user_id and public.emlis_parent_visible(e.created_at,profile.tier,statement_timestamp())
      and (record_fields.thought ~ '[^[:space:]]' or record_fields.action ~ '[^[:space:]]'
        or answers.items is not null or corrections.items is not null)
      and coalesce(t.data->>'body_state','') <> 'SAFETY'
    order by e.created_at desc,e.id limit 8
  ), prior as (
    select q.id,q.lane,q.theme,q.question_text,q.answer_text,q.answered_at,q.issued_at,q.question_key,q.text_key,
      q.grounding_receipt,
      case when q.answered_at is not null then encode(sha256(convert_to(jsonb_build_array(
        q.id,q.question_text,q.answer_text,q.answered_at)::text,'UTF8')),'hex') end as source_version
    from public.deep_insight_questions q where q.user_id=p_user_id
    order by q.issued_at desc,q.id limit 30
  ), map_guard as materialized (
    select case when profile.available and exists(select 1 from public.analysis_observed_artifacts
      where user_id=p_user_id and source_profile='cumulative.v1')
      then public.analysis_cumulative_source_snapshot(p_user_id)->>'guard' end as value
    from profile
  ), map as (
    select jsonb_build_object('id',a.id,'generated_at',a.generated_at,
      'source_version',encode(sha256(convert_to(a.source_guard,'UTF8')),'hex'),
      'summary',left(a.content_text,1800)) as item
    from public.analysis_observed_artifacts a cross join map_guard
    where a.user_id=p_user_id and a.source_profile='cumulative.v1'
      and a.id=public.analysis_cumulative_current_id(p_user_id,map_guard.value)
    order by a.generated_at desc,a.id desc limit 1
  )
  select jsonb_build_object(
    'records',coalesce((select jsonb_agg(to_jsonb(r)-array_remove(array[
        case when r.emlis_skipped_question is null then 'emlis_skipped_question' end,
        case when r.emlis_corrections is null then 'emlis_corrections' end],null)
        order by r.created_at desc,r.id)
      from records r),'[]'::jsonb),
    'prior',coalesce((select jsonb_agg(to_jsonb(p) order by p.issued_at desc,p.id) from prior p),'[]'::jsonb),
    'map',(select item from map));
$$;

commit;
