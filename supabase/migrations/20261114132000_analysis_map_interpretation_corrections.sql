-- A person's correction of a saved map is its own source. The selected AI
-- wording is immutable control, not a new emotion or an Emlis answer. Old
-- artifacts/monthly references are never updated by this write path.
begin;

create table public.analysis_map_interpretation_corrections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  idempotency_key text not null check (char_length(idempotency_key) between 1 and 128
    and btrim(idempotency_key) <> ''),
  request_body jsonb not null check (jsonb_typeof(request_body) = 'object'),
  recorded_at timestamptz not null default statement_timestamp(),
  target_context jsonb not null check (jsonb_typeof(target_context) = 'object'),
  explanation text not null check (char_length(explanation) between 1 and 2000
    and btrim(explanation) <> ''),
  unique(user_id,idempotency_key)
);
create index analysis_map_correction_owner_order
  on public.analysis_map_interpretation_corrections(user_id,recorded_at,id);
alter table public.analysis_map_interpretation_corrections enable row level security;
revoke all on public.analysis_map_interpretation_corrections from public,anon,authenticated,service_role;
grant select on public.analysis_map_interpretation_corrections to service_role;

create function public.analysis_map_correction_immutable() returns trigger
language plpgsql set search_path='' as $$
begin
  raise sqlstate '55000' using message='analysis_map_correction_immutable';
end;
$$;
create trigger analysis_map_correction_no_update
  before update on public.analysis_map_interpretation_corrections
  for each row execute function public.analysis_map_correction_immutable();

-- Map wording can reproduce private input. Deleting a dependency or moving it
-- away from its owner therefore erases the whole derived correction row,
-- including target control, request body and person explanation. An ordinary
-- edit only makes it STALE; replacing an artifact cache does not erase it.
create function public.analysis_map_correction_source_deleted() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if TG_OP='UPDATE' and OLD.user_id is not distinct from NEW.user_id then return null; end if;
  delete from public.analysis_map_interpretation_corrections c
    where c.user_id=old.user_id and exists (
      select 1 from jsonb_array_elements(c.target_context->'cohort') dependency
        where dependency->>'record_ref'=old.id::text);
  return null;
end;
$$;
create trigger analysis_map_correction_source_delete
  after delete or update of user_id on public.emotions
  for each row execute function public.analysis_map_correction_source_deleted();

-- p_members is the caller's already-frozen cumulative snapshot. This function
-- must not call analysis_cumulative_source_snapshot: that owner adds these
-- rows after obtaining its ordinary members. Revision and the context clock
-- are transport state, not a change in the person's source cohort.
create function public.analysis_map_correction_sources(p_user_id uuid,p_members jsonb)
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
      select 1 from jsonb_array_elements(c.target_context->'cohort') dependency
      where (select count(*) from jsonb_array_elements(p_members) member
        where member#>>'{original,id}' = dependency->>'record_ref'
          and 'analysis-map-member-v1:' || encode(sha256(convert_to(
            (member #- '{thread,revision}' #- '{context,now}')::text,'UTF8')),'hex')
              = dependency->>'source_guard') <> 1
      ) then 'ACTIVE' else 'STALE' end) order by c.recorded_at,c.id),'[]'::jsonb)
    into result from public.analysis_map_interpretation_corrections c
    where c.user_id=p_user_id;
  return result;
end;
$$;

create function public.analysis_map_correction_read(p_user_id uuid,p_key text)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare snap jsonb; result jsonb;
begin
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select row into result from jsonb_array_elements(
    public.analysis_map_correction_sources(p_user_id,snap->'members')) row
    where row->>'correction_id'=(select id::text
      from public.analysis_map_interpretation_corrections
      where user_id=p_user_id and idempotency_key=p_key);
  if result is null then
    raise sqlstate 'P0002' using message='analysis_map_correction_unavailable';
  end if;
  return result;
end;
$$;

create function public.analysis_map_correction_submit(
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
  if artifact.source_guard is distinct from snap->>'guard' then
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
      'source_guard','analysis-map-member-v1:' || encode(sha256(convert_to(
        (member #- '{thread,revision}' #- '{context,now}')::text,'UTF8')),'hex'))
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

revoke all on function public.analysis_map_correction_immutable() from public,anon,authenticated,service_role;
revoke all on function public.analysis_map_correction_source_deleted() from public,anon,authenticated,service_role;
revoke all on function public.analysis_map_correction_sources(uuid,jsonb) from public,anon,authenticated;
revoke all on function public.analysis_map_correction_read(uuid,text) from public,anon,authenticated;
revoke all on function public.analysis_map_correction_submit(uuid,text,text,text,text,text,text,text) from public,anon,authenticated;
grant execute on function public.analysis_map_correction_sources(uuid,jsonb),
  public.analysis_map_correction_read(uuid,text),
  public.analysis_map_correction_submit(uuid,text,text,text,text,text,text,text) to service_role;

commit;
