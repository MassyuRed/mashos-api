-- IF and explicit Saved intentions have their own immutable identities.
-- No observed row, current/monthly pointer, source input or entitlement is changed.
begin;

create table public.analysis_if_scenario_sets (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  artifact_ref text unique,
  scenario_set_ref text unique,
  base_observed_map_ref text not null,
  base_source_guard text not null check (base_source_guard ~ '^analysis-db-cumulative-v1:[0-9a-f]{64}$'),
  source_record_refs jsonb not null check (jsonb_typeof(source_record_refs)='array' and jsonb_array_length(source_record_refs)>0),
  request_key_hash text not null check (request_key_hash ~ '^[0-9a-f]{64}$'),
  request_hash text not null check (request_hash ~ '^[0-9a-f]{64}$'),
  operation_state text not null default 'RESERVED'
    check (operation_state in ('RESERVED','CALL_STARTED','RECEIVED','COMPLETED','FAILED')),
  call_token uuid,
  operation_material jsonb,
  provider_receipt jsonb,
  base_projection jsonb,
  base_private_evidence jsonb,
  storage jsonb,
  created_at timestamptz not null default clock_timestamp(),
  deleted_at timestamptz,
  unique(user_id,request_key_hash),
  check (artifact_ref='artifact:' || replace(id::text,'-','') || '@1'),
  check (scenario_set_ref ~ '^scenario-set:[^@]+@1$'),
  check ((
    (deleted_at is not null and storage is null and operation_material is null
      and provider_receipt is null and base_projection is null and base_private_evidence is null and call_token is null)
    or (deleted_at is null and operation_state='COMPLETED' and artifact_ref is not null
      and scenario_set_ref is not null and jsonb_typeof(storage)='object' and octet_length(storage::text)<=2097152
      and operation_material is null and provider_receipt is null and base_projection is null
      and base_private_evidence is null and call_token is null)
    or (deleted_at is null and operation_state in ('RESERVED','CALL_STARTED','RECEIVED')
      and artifact_ref is null and scenario_set_ref is null and storage is null and call_token is not null
      and jsonb_typeof(operation_material)='object' and octet_length(operation_material::text)<=2097152
      and jsonb_typeof(base_projection)='object' and jsonb_typeof(base_private_evidence)='object'
      and ((operation_state='RECEIVED' and jsonb_typeof(provider_receipt)='object'
            and octet_length(provider_receipt::text)<=2097152)
        or (operation_state in ('RESERVED','CALL_STARTED') and provider_receipt is null)))
    or (deleted_at is null and operation_state='FAILED' and artifact_ref is null
      and scenario_set_ref is null and storage is null and call_token is null
      and operation_material is null and provider_receipt is null and base_projection is null
      and base_private_evidence is null)
  ) is true)
);
create index analysis_if_sets_owner on public.analysis_if_scenario_sets(user_id,created_at desc,id);

create table public.analysis_saved_route_intents (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  scenario_set_id uuid not null references public.analysis_if_scenario_sets(id) on delete cascade,
  artifact_ref text not null unique,
  selected_scenario_ref text not null,
  request_key_hash text not null check (request_key_hash ~ '^[0-9a-f]{64}$'),
  request_hash text not null check (request_hash ~ '^[0-9a-f]{64}$'),
  storage jsonb,
  created_at timestamptz not null default clock_timestamp(),
  deleted_at timestamptz,
  unique(user_id,request_key_hash),
  check (artifact_ref='artifact:' || replace(id::text,'-','') || '@1'),
  check (selected_scenario_ref ~ '^analysis-if-scenario:[^@]+@1$'),
  check (((deleted_at is null and jsonb_typeof(storage)='object' and octet_length(storage::text)<=2097152)
      or (deleted_at is not null and storage is null)) is true)
);
create index analysis_if_intents_owner on public.analysis_saved_route_intents(user_id,created_at desc,id);
create index analysis_if_intents_parent on public.analysis_saved_route_intents(scenario_set_id);
alter table public.analysis_if_scenario_sets enable row level security;
alter table public.analysis_saved_route_intents enable row level security;
revoke all on public.analysis_if_scenario_sets,public.analysis_saved_route_intents from public,anon,authenticated,service_role;
grant select,insert,update,delete on public.analysis_if_scenario_sets,public.analysis_saved_route_intents to service_role;

-- UPDATE is needed for pending operations and body-free deletion, never for
-- rewriting a completed artifact or reviving a deleted operation identity.
create function public.analysis_if_completed_immutable() returns trigger
language plpgsql set search_path='' as $$
declare before_row jsonb:=to_jsonb(OLD); after_row jsonb:=to_jsonb(NEW);
  private_keys text[]:=array['storage','operation_material','provider_receipt','base_projection','base_private_evidence','call_token'];
begin
  if before_row=after_row then return NEW; end if;
  if OLD.deleted_at is not null then raise sqlstate '23505' using message='analysis_if_deleted_immutable'; end if;
  if before_row->>'operation_state'='COMPLETED' or TG_TABLE_NAME='analysis_saved_route_intents' then
    if NEW.deleted_at is null
      or before_row-(private_keys || array['deleted_at']) is distinct from after_row-(private_keys || array['deleted_at'])
      or jsonb_strip_nulls(after_row) ?| private_keys then
      raise sqlstate '23505' using message='analysis_if_artifact_immutable'; end if;
  end if;
  return NEW;
end;
$$;
create trigger analysis_if_set_immutable before update on public.analysis_if_scenario_sets
  for each row execute function public.analysis_if_completed_immutable();
create trigger analysis_if_intent_immutable before update on public.analysis_saved_route_intents
  for each row execute function public.analysis_if_completed_immutable();
revoke all on function public.analysis_if_completed_immutable() from public,anon,authenticated;

create function public.analysis_if_require_premium(p_user_id uuid)
returns void language plpgsql stable security invoker set search_path='' as $$
begin
  if not exists(select 1 from public.profiles where id=p_user_id and subscription_tier='premium') then
    raise sqlstate '42501' using message='analysis_if_access_unavailable';
  end if;
end;
$$;

-- Current-map replacement must not erase a person's saved intention. Pin the
-- parent's source cohort, not an FK to the prunable current-map cache. Rebuild
-- its existing DB-native commitment from those exact current source members:
-- a new, unrelated input is not an edit, answer revision or deletion of them.
create function public.analysis_if_sources_current(p_user_id uuid,p_guard text,p_refs jsonb)
returns boolean language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; members jsonb; guard text;
begin
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select coalesce(jsonb_agg(m #- '{thread,revision}' order by ord),'[]'::jsonb) into members
    from jsonb_array_elements(snap->'members') with ordinality as x(m,ord)
    where p_refs ? (m#>>'{original,id}');
  guard:='analysis-db-cumulative-v1:' || encode(sha256(convert_to(
    jsonb_build_object('owner',p_user_id,'members',members)::text,'UTF8')),'hex');
  return guard=p_guard and jsonb_array_length(members)=jsonb_array_length(p_refs);
end;
$$;

-- This result is server-private. HTTP never serializes the base private JSON.
create function public.analysis_if_base_context(p_user_id uuid,p_base_ref text)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; parent public.analysis_observed_artifacts; refs jsonb;
begin
  perform public.analysis_if_require_premium(p_user_id);
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select * into parent from public.analysis_observed_artifacts where user_id=p_user_id
    and artifact_id || '@' || artifact_version::text=p_base_ref and source_profile='cumulative.v1'
    and source_guard=snap->>'guard';
  if not found then raise sqlstate 'P0002' using message='analysis_if_base_unavailable'; end if;
  select coalesce(jsonb_agg(m#>>'{original,id}' order by ord),'[]'::jsonb) into refs
    from jsonb_array_elements(snap->'members') with ordinality as x(m,ord);
  if jsonb_array_length(refs)=0 then raise sqlstate 'P0002' using message='analysis_if_base_unavailable'; end if;
  return jsonb_build_object('base_observed_map_ref',p_base_ref,'base_source_guard',parent.source_guard,
    'base_projection',parent.safe_projection,'base_private_evidence',parent.private_evidence,
    'source_record_refs',refs,'subscription_tier',snap->>'tier');
end;
$$;

-- One durable row owns one provider call across HTTP retries and API processes.
-- A lost reserve/start ACK never issues a second token; RECEIVED replays the
-- exact prepared material and receipt, so admission/commit can resume offline.
create function public.analysis_if_operation_reserve(p_user_id uuid,p_key_hash text,p_request_hash text,
  p_base_ref text default null,p_guard text default null,p_material jsonb default null)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare old public.analysis_if_scenario_sets; base jsonb; operation_id uuid; token uuid;
begin
  if current_setting('transaction_isolation')<>'read committed' then raise sqlstate '40001'; end if;
  if p_key_hash is null or p_key_hash !~ '^[0-9a-f]{64}$'
    or p_request_hash is null or p_request_hash !~ '^[0-9a-f]{64}$' then raise sqlstate '22023'; end if;
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events in share mode nowait;
  perform public.analysis_if_require_premium(p_user_id);
  select * into old from public.analysis_if_scenario_sets where user_id=p_user_id and request_key_hash=p_key_hash;
  if found then
    if old.request_hash is distinct from p_request_hash then raise sqlstate '23505' using message='analysis_if_request_conflict'; end if;
    if old.deleted_at is not null then raise sqlstate 'P0002' using message='analysis_if_request_deleted'; end if;
    if not public.analysis_if_sources_current(p_user_id,old.base_source_guard,old.source_record_refs) then
      raise sqlstate '40001' using message='analysis_if_source_changed'; end if;
    return jsonb_build_object('state',old.operation_state,'operation_id',old.id,'call_token',null,
      'material',case when old.operation_state='RECEIVED' then old.operation_material else null end,
      'receipt',case when old.operation_state='RECEIVED' then old.provider_receipt else null end,
      'artifact_id',case when old.operation_state='COMPLETED' then old.id else null end);
  end if;
  if p_material is null then return null; end if;
  base:=public.analysis_if_base_context(p_user_id,p_base_ref);
  if base->>'base_source_guard' is distinct from p_guard then raise sqlstate '40001'; end if;
  if (jsonb_typeof(p_material)='object'
      and p_material ?& array['request','request_ref','messages_json','base_seed_json']
      and p_material-array['request','request_ref','messages_json','base_seed_json']='{}'::jsonb
      and jsonb_typeof(p_material->'request')='object'
      and jsonb_typeof(p_material->'request_ref')='string'
      and jsonb_typeof(p_material->'messages_json')='string'
      and jsonb_typeof(p_material->'base_seed_json')='string'
      and p_material#>>'{request,authenticated_owner_scope}'=p_user_id::text
      and p_material#>>'{request,base_observed_map_ref}'=p_base_ref
      and p_material#>>'{request,base_source_guard}'=p_guard) is not true then
    raise sqlstate '22023' using message='analysis_if_operation_invalid'; end if;
  if (p_material#>>'{request,base_projection_json}')::jsonb is distinct from base->'base_projection'
    or (p_material#>>'{request,base_private_evidence_json}')::jsonb is distinct from base->'base_private_evidence' then
    raise sqlstate '22023' using message='analysis_if_operation_invalid'; end if;
  operation_id:=gen_random_uuid(); token:=gen_random_uuid();
  insert into public.analysis_if_scenario_sets(id,user_id,base_observed_map_ref,base_source_guard,
    source_record_refs,request_key_hash,request_hash,operation_state,call_token,operation_material,
    base_projection,base_private_evidence)
    values(operation_id,p_user_id,p_base_ref,p_guard,base->'source_record_refs',p_key_hash,p_request_hash,
      'RESERVED',token,p_material,base->'base_projection',base->'base_private_evidence');
  return jsonb_build_object('state','RESERVED','operation_id',operation_id,'call_token',token,
    'material',null,'receipt',null,'artifact_id',null);
exception when lock_not_available or deadlock_detected then raise sqlstate '40001' using message='analysis_if_source_busy';
end;
$$;

create function public.analysis_if_operation_start(p_user_id uuid,p_key_hash text,p_token uuid)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare old public.analysis_if_scenario_sets;
begin
  if current_setting('transaction_isolation')<>'read committed' then raise sqlstate '40001'; end if;
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events in share mode nowait;
  perform public.analysis_if_require_premium(p_user_id);
  select * into old from public.analysis_if_scenario_sets where user_id=p_user_id and request_key_hash=p_key_hash;
  if not found or old.deleted_at is not null then raise sqlstate 'P0002'; end if;
  if not public.analysis_if_sources_current(p_user_id,old.base_source_guard,old.source_record_refs) then raise sqlstate '40001'; end if;
  if old.operation_state<>'RESERVED' or p_token is null or old.call_token is distinct from p_token then
    return jsonb_build_object('started',false); end if;
  update public.analysis_if_scenario_sets set operation_state='CALL_STARTED' where id=old.id;
  return jsonb_build_object('started',true);
exception when lock_not_available or deadlock_detected then raise sqlstate '40001' using message='analysis_if_source_busy';
end;
$$;

create function public.analysis_if_operation_receive(p_user_id uuid,p_key_hash text,p_token uuid,p_receipt jsonb)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare old public.analysis_if_scenario_sets;
begin
  if current_setting('transaction_isolation')<>'read committed' then raise sqlstate '40001'; end if;
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events in share mode nowait;
  perform public.analysis_if_require_premium(p_user_id);
  select * into old from public.analysis_if_scenario_sets where user_id=p_user_id and request_key_hash=p_key_hash;
  if not found or old.deleted_at is not null then raise sqlstate 'P0002'; end if;
  if not public.analysis_if_sources_current(p_user_id,old.base_source_guard,old.source_record_refs) then raise sqlstate '40001'; end if;
  if p_token is null or old.call_token is distinct from p_token then return jsonb_build_object('received',false); end if;
  if old.operation_state='RECEIVED' then
    if old.provider_receipt is distinct from p_receipt then raise sqlstate '23505' using message='analysis_if_receipt_conflict'; end if;
    return jsonb_build_object('received',true);
  end if;
  if old.operation_state<>'CALL_STARTED' then return jsonb_build_object('received',false); end if;
  if (jsonb_typeof(p_receipt)='object' and p_receipt ?& array['request_ref','messages_sha256','raw_sha256','finish_reason','raw']
      and p_receipt-array['request_ref','messages_sha256','raw_sha256','finish_reason','raw']='{}'::jsonb
      and p_receipt->>'request_ref'=old.operation_material->>'request_ref'
      and jsonb_typeof(p_receipt->'raw')='string') is not true then
    raise sqlstate '22023' using message='analysis_if_receipt_invalid'; end if;
  update public.analysis_if_scenario_sets set operation_state='RECEIVED',provider_receipt=p_receipt where id=old.id;
  return jsonb_build_object('received',true);
exception when lock_not_available or deadlock_detected then raise sqlstate '40001' using message='analysis_if_source_busy';
end;
$$;

create function public.analysis_if_operation_fail(p_user_id uuid,p_key_hash text,p_token uuid)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare old public.analysis_if_scenario_sets;
begin
  if current_setting('transaction_isolation')<>'read committed' then raise sqlstate '40001'; end if;
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events in share mode nowait;
  perform public.analysis_if_require_premium(p_user_id);
  select * into old from public.analysis_if_scenario_sets where user_id=p_user_id and request_key_hash=p_key_hash;
  if not found or old.deleted_at is not null then raise sqlstate 'P0002'; end if;
  if not public.analysis_if_sources_current(p_user_id,old.base_source_guard,old.source_record_refs) then raise sqlstate '40001'; end if;
  if old.operation_state not in ('RESERVED','CALL_STARTED') or p_token is null or old.call_token is distinct from p_token then
    return jsonb_build_object('failed',false); end if;
  update public.analysis_if_scenario_sets set operation_state='FAILED',call_token=null,
    operation_material=null,provider_receipt=null,base_projection=null,base_private_evidence=null where id=old.id;
  return jsonb_build_object('failed',true);
exception when lock_not_available or deadlock_detected then raise sqlstate '40001' using message='analysis_if_source_busy';
end;
$$;

create function public.analysis_if_artifacts_read(p_user_id uuid,p_kind text,p_id uuid default null,
  p_limit integer default 60,p_offset integer default 0,p_key_hash text default null,p_request_hash text default null,p_set_ref text default null)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare items jsonb; row_data record; parent public.analysis_if_scenario_sets; skipped integer:=0;
begin
  perform public.analysis_if_require_premium(p_user_id);
  if p_kind not in ('scenario_set','saved_intent') or p_limit not between 1 and 100 or p_offset not between 0 and 10000 then
    raise sqlstate '22023' using message='analysis_if_request_invalid'; end if;
  items:='[]'::jsonb;
  for row_data in
    select s.id,s.storage,s.created_at,s.deleted_at,s.request_hash,s.id as parent_id,s.operation_state
      from public.analysis_if_scenario_sets s where p_kind='scenario_set' and s.user_id=p_user_id
      and (p_id is null or s.id=p_id) and (p_key_hash is null or s.request_key_hash=p_key_hash)
      and (p_set_ref is null or s.scenario_set_ref=p_set_ref)
    union all
    select i.id,i.storage,i.created_at,i.deleted_at,i.request_hash,i.scenario_set_id,'COMPLETED'::text
      from public.analysis_saved_route_intents i where p_kind='saved_intent' and i.user_id=p_user_id
      and (p_id is null or i.id=p_id) and (p_key_hash is null or i.request_key_hash=p_key_hash)
    order by created_at desc,id desc
  loop
    if p_key_hash is not null and row_data.request_hash is distinct from p_request_hash then
      raise sqlstate '23505' using message='analysis_if_request_conflict'; end if;
    if row_data.deleted_at is not null then
      if p_key_hash is not null then raise sqlstate 'P0002' using message='analysis_if_request_deleted'; end if;
      continue;
    end if;
    if row_data.operation_state<>'COMPLETED' then continue; end if;
    select * into parent from public.analysis_if_scenario_sets where id=row_data.parent_id and user_id=p_user_id;
    if not found or parent.deleted_at is not null or not public.analysis_if_sources_current(
      p_user_id,parent.base_source_guard,parent.source_record_refs) then
      if p_key_hash is not null then raise sqlstate '40001' using message='analysis_if_source_changed'; end if;
      continue;
    end if;
    if skipped<p_offset then skipped:=skipped+1; continue; end if;
    items:=items || jsonb_build_array(jsonb_build_object('id',row_data.id,'storage',row_data.storage,'created_at',row_data.created_at));
    if jsonb_array_length(items)>=p_limit then exit; end if;
  end loop;
  return jsonb_build_object('items',items,'subscription_tier','premium');
end;
$$;

create function public.analysis_if_set_commit(p_user_id uuid,p_base_ref text,p_guard text,
  p_key_hash text,p_request_hash text,p_storage jsonb)
returns uuid language plpgsql volatile security definer set search_path='' as $$
declare old public.analysis_if_scenario_sets; ref text; set_ref text; rid uuid;
begin
  if current_setting('transaction_isolation')<>'read committed' then raise sqlstate '40001'; end if;
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events in share mode nowait;
  perform public.analysis_if_require_premium(p_user_id);
  select * into old from public.analysis_if_scenario_sets where user_id=p_user_id and request_key_hash=p_key_hash;
  if not found then raise sqlstate 'P0002' using message='analysis_if_operation_unavailable'; end if;
  if old.request_hash is distinct from p_request_hash or old.deleted_at is not null then raise sqlstate '23505'; end if;
  if not public.analysis_if_sources_current(p_user_id,old.base_source_guard,old.source_record_refs) then raise sqlstate '40001'; end if;
  if old.operation_state='COMPLETED' then return old.id; end if;
  if old.operation_state<>'RECEIVED' then raise sqlstate '40001' using message='analysis_if_receipt_required'; end if;
  if old.base_observed_map_ref is distinct from p_base_ref or old.base_source_guard is distinct from p_guard then
    raise sqlstate '40001' using message='analysis_if_source_changed'; end if;
  ref:=p_storage#>>'{safe_projection,projection_of}';
  set_ref:=(p_storage#>>'{bundle,primary_artifact,candidate_set_id}') || '@1';
  if ref is null or ref !~ '^artifact:[0-9a-f]{32}@1$'
    or set_ref is null or set_ref !~ '^scenario-set:[^@]+@1$'
    or p_storage->>'owner_scope' is distinct from p_user_id::text
    or p_storage->>'schema_version' is distinct from 'analysis.if-storage.v1'
    or p_storage#>>'{bundle,lifecycle_bindings,version_set,base_source_guard}' is distinct from p_guard
    or p_storage->'base_projection' is distinct from old.base_projection
    or p_storage->'base_private_evidence' is distinct from old.base_private_evidence
    or p_storage->'model_receipt' is distinct from old.provider_receipt
    or p_storage#>>'{safe_projection,wire_kind}' is distinct from 'watashi.if-route-set.v1'
    or p_storage#>>'{safe_projection,base_observed_map_ref}' is distinct from p_base_ref then
    raise sqlstate '22023' using message='analysis_if_artifact_invalid'; end if;
  rid:=substring(ref from 10 for 32)::uuid;
  update public.analysis_if_scenario_sets set id=rid,artifact_ref=ref,scenario_set_ref=set_ref,
    storage=p_storage,operation_state='COMPLETED',operation_material=null,provider_receipt=null,
    base_projection=null,base_private_evidence=null,call_token=null where id=old.id;
  return rid;
exception when lock_not_available or deadlock_detected then raise sqlstate '40001' using message='analysis_if_source_busy';
end;
$$;

create function public.analysis_if_intent_commit(p_user_id uuid,p_set_ref text,p_key_hash text,p_request_hash text,p_storage jsonb)
returns uuid language plpgsql volatile security definer set search_path='' as $$
declare parent public.analysis_if_scenario_sets; old public.analysis_saved_route_intents; ref text; chosen text; rid uuid;
begin
  if current_setting('transaction_isolation')<>'read committed' then raise sqlstate '40001'; end if;
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events in share mode nowait;
  perform public.analysis_if_require_premium(p_user_id);
  select * into parent from public.analysis_if_scenario_sets where user_id=p_user_id and scenario_set_ref=p_set_ref
    and operation_state='COMPLETED' and deleted_at is null;
  if not found then raise sqlstate 'P0002'; end if;
  if not public.analysis_if_sources_current(p_user_id,parent.base_source_guard,parent.source_record_refs) then raise sqlstate '40001'; end if;
  select * into old from public.analysis_saved_route_intents where user_id=p_user_id and request_key_hash=p_key_hash;
  if found then
    if old.request_hash is distinct from p_request_hash or old.deleted_at is not null then raise sqlstate '23505'; end if;
    return old.id;
  end if;
  ref:=p_storage#>>'{safe_projection,projection_of}';
  chosen:=p_storage#>>'{bundle,primary_artifact,selected_scenario_ref}';
  if ref is null or ref !~ '^artifact:[0-9a-f]{32}@1$'
    or p_storage->>'schema_version' is distinct from 'analysis.if-storage.v1'
    or p_storage->>'owner_scope' is distinct from p_user_id::text
    or p_storage#>>'{bundle,lifecycle_bindings,version_set,base_source_guard}' is distinct from parent.base_source_guard
    or p_storage->'base_projection' is distinct from parent.storage->'base_projection'
    or p_storage->'base_private_evidence' is distinct from parent.storage->'base_private_evidence'
    or p_storage#>>'{safe_projection,wire_kind}' is distinct from 'watashi.saved-route-intent.v1'
    or p_storage#>>'{safe_projection,source_scenario_set_ref}' is distinct from p_set_ref
    or not exists(select 1 from jsonb_array_elements(parent.storage#>'{bundle,primary_artifact,scenarios}') s
      where s->>'scenario_artifact_ref'=chosen) then raise sqlstate '22023' using message='analysis_if_selection_invalid'; end if;
  rid:=substring(ref from 10 for 32)::uuid;
  insert into public.analysis_saved_route_intents(id,user_id,scenario_set_id,artifact_ref,selected_scenario_ref,
    request_key_hash,request_hash,storage) values(rid,p_user_id,parent.id,ref,chosen,p_key_hash,p_request_hash,p_storage);
  return rid;
exception when lock_not_available or deadlock_detected then raise sqlstate '40001' using message='analysis_if_source_busy';
end;
$$;

create function public.analysis_if_artifact_delete(p_user_id uuid,p_kind text,p_id uuid)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare affected integer;
begin
  -- A downgrade blocks paid reads/generation, not deletion of one's own data.
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002'; end if;
  if p_kind='scenario_set' then
    update public.analysis_if_scenario_sets set storage=null,operation_material=null,provider_receipt=null,
      base_projection=null,base_private_evidence=null,call_token=null,deleted_at=coalesce(deleted_at,clock_timestamp())
      where id=p_id and user_id=p_user_id;
    get diagnostics affected=row_count;
    update public.analysis_saved_route_intents set storage=null,deleted_at=coalesce(deleted_at,clock_timestamp())
      where scenario_set_id=p_id and user_id=p_user_id;
  elsif p_kind='saved_intent' then
    update public.analysis_saved_route_intents set storage=null,deleted_at=coalesce(deleted_at,clock_timestamp())
      where id=p_id and user_id=p_user_id;
    get diagnostics affected=row_count;
  else raise sqlstate '22023'; end if;
  if affected=0 then raise sqlstate 'P0002'; end if;
  return jsonb_build_object('deleted',true,'id',p_id);
exception when lock_not_available or deadlock_detected then raise sqlstate '40001';
end;
$$;

-- Input deletion removes derivative private content as well as denying reads.
-- Keep only body-free operation tombstones, so a late retry cannot resurrect it.
create function public.analysis_if_source_deleted() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if TG_OP='UPDATE' and OLD.user_id is not distinct from NEW.user_id then return null; end if;
  update public.analysis_if_scenario_sets set storage=null,operation_material=null,provider_receipt=null,
    base_projection=null,base_private_evidence=null,call_token=null,deleted_at=coalesce(deleted_at,clock_timestamp())
    where user_id=OLD.user_id and source_record_refs ? OLD.id::text;
  update public.analysis_saved_route_intents i set storage=null,deleted_at=coalesce(i.deleted_at,clock_timestamp())
    from public.analysis_if_scenario_sets s where i.scenario_set_id=s.id
      and s.user_id=OLD.user_id and s.source_record_refs ? OLD.id::text;
  return null;
end;
$$;
create trigger analysis_if_input_deleted after delete or update of user_id on public.emotions
  for each row execute function public.analysis_if_source_deleted();
revoke all on function public.analysis_if_source_deleted() from public,anon,authenticated;

revoke all on function public.analysis_if_require_premium(uuid), public.analysis_if_sources_current(uuid,text,jsonb),
  public.analysis_if_base_context(uuid,text),public.analysis_if_artifacts_read(uuid,text,uuid,integer,integer,text,text,text),
  public.analysis_if_operation_reserve(uuid,text,text,text,text,jsonb),public.analysis_if_operation_start(uuid,text,uuid),
  public.analysis_if_operation_receive(uuid,text,uuid,jsonb),public.analysis_if_operation_fail(uuid,text,uuid),
  public.analysis_if_set_commit(uuid,text,text,text,text,jsonb),public.analysis_if_intent_commit(uuid,text,text,text,jsonb),
  public.analysis_if_artifact_delete(uuid,text,uuid) from public,anon,authenticated;
grant execute on function public.analysis_if_require_premium(uuid), public.analysis_if_sources_current(uuid,text,jsonb),
  public.analysis_if_base_context(uuid,text),public.analysis_if_artifacts_read(uuid,text,uuid,integer,integer,text,text,text),
  public.analysis_if_operation_reserve(uuid,text,text,text,text,jsonb),public.analysis_if_operation_start(uuid,text,uuid),
  public.analysis_if_operation_receive(uuid,text,uuid,jsonb),public.analysis_if_operation_fail(uuid,text,uuid),
  public.analysis_if_set_commit(uuid,text,text,text,text,jsonb),public.analysis_if_intent_commit(uuid,text,text,text,jsonb),
  public.analysis_if_artifact_delete(uuid,text,uuid) to service_role;
commit;
