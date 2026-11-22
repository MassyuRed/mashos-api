-- Candidate only: apply separately before enabling comparison generation.
-- No new table, public wire field, or rewrite of existing saved artifacts.
begin;
alter table public.analysis_observed_artifacts
  drop constraint analysis_observed_artifacts_source_guard_check,
  add constraint analysis_observed_artifacts_source_guard_check
    check (source_guard ~ '^analysis-db-(v1|compare-v1):[0-9a-f]{64}$'),
  drop constraint analysis_observed_artifacts_check2,
  add constraint analysis_observed_artifacts_private_evidence_check check (
    (jsonb_typeof(private_evidence)='object'
      and private_evidence->>'schema_version' in ('analysis.private-evidence.v1','analysis.private-evidence.v2')
      and private_evidence->>'projection_of'=artifact_id || '@' || artifact_version::text) is true);

-- One MVCC statement snapshot for both source sets. Equal duration is computed
-- in UTC, not calendar days in the caller's session time zone.
create function public.analysis_observed_comparison_snapshot(
  p_user_id uuid,p_start timestamptz,p_end timestamptz,p_mode text,p_report_type text)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare current_source jsonb; previous_source jsonb; previous_start timestamptz;
begin
  current_source := public.analysis_observed_source_snapshot(p_user_id,p_start,p_end,p_mode,p_report_type);
  previous_start := ((p_start at time zone 'UTC')-
    ((p_end at time zone 'UTC')-(p_start at time zone 'UTC'))) at time zone 'UTC';
  -- Comparison must not remove an otherwise available current map at a plan's
  -- retention boundary. This is explicit eligibility, not an error fallback.
  if not public.emlis_parent_visible(previous_start at time zone 'UTC',
    current_source->>'tier',statement_timestamp()) then
    return jsonb_build_object('comparison_eligible',false,'current',current_source,
      'tier',current_source->>'tier','guard',current_source->>'guard');
  end if;
  previous_source := public.analysis_observed_source_snapshot(p_user_id,previous_start,p_start,p_mode,p_report_type);
  return jsonb_build_object('comparison_eligible',true,'current',current_source,'previous',previous_source,
    'previous_start',previous_start,'previous_end',p_start,'tier',current_source->>'tier','guard',
    'analysis-db-compare-v1:' || encode(sha256(convert_to(jsonb_build_object(
      'policy','adjacent-equal-v1','current_guard',current_source->>'guard',
      'previous_guard',previous_source->>'guard')::text,'UTF8')),'hex'));
end;
$$;

create or replace function public.analysis_observed_commit(
  p_user_id uuid,p_start timestamptz,p_end timestamptz,p_mode text,p_report_type text,
  p_guard text,p_artifact_id text,p_private_evidence jsonb,p_projection jsonb,p_text text)
returns uuid language plpgsql volatile security definer set search_path='' as $$
declare snap jsonb; rid uuid; existing uuid; c jsonb; previous jsonb; changes jsonb;
begin
  if current_setting('transaction_isolation') <> 'read committed' then
    raise sqlstate '40001' using message='analysis_isolation_unavailable'; end if;
  perform 1 from auth.users where id=p_user_id for key share nowait;
  if not found then raise sqlstate 'P0002' using message='analysis_owner_unavailable'; end if;
  lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events
    in share mode nowait;
  if p_guard like 'analysis-db-compare-v1:%' then
    snap := public.analysis_observed_comparison_snapshot(p_user_id,p_start,p_end,p_mode,p_report_type);
  else
    snap := public.analysis_observed_source_snapshot(p_user_id,p_start,p_end,p_mode,p_report_type);
  end if;
  if snap->>'guard' is distinct from p_guard then
    raise sqlstate '40001' using message='analysis_source_changed'; end if;
  if p_artifact_id !~ '^artifact:[0-9a-f]{32}$' or p_artifact_id is null then
    raise sqlstate '22023' using message='analysis_identity_invalid'; end if;
  if p_guard like 'analysis-db-compare-v1:%' then
    if (p_private_evidence->>'schema_version'='analysis.private-evidence.v2'
      and (p_private_evidence->'comparison_dependency') - array[
        'policy','previous_period_start','previous_period_end']='{}'::jsonb
      and p_private_evidence->'comparison_dependency'->>'policy'='adjacent-equal-v1'
      and (p_private_evidence->'comparison_dependency'->>'previous_period_start')::timestamptz=
        (snap->>'previous_start')::timestamptz
      and (p_private_evidence->'comparison_dependency'->>'previous_period_end')::timestamptz=p_start) is not true then
      raise sqlstate '23514' using message='analysis_comparison_dependency_invalid'; end if;
    c := p_private_evidence->'period_comparison';
    previous := p_private_evidence->'previous_evidence';
    if jsonb_array_length(snap->'previous'->'members')=0 then
      if (c='null'::jsonb and previous='null'::jsonb and p_projection->'period_comparison'=
        '{"state":"NO_PREVIOUS","reason_codes":[],"safe_change_kinds":[]}'::jsonb) is not true then
        raise sqlstate '23514' using message='analysis_comparison_empty_invalid'; end if;
    else
      if (jsonb_typeof(c)='object' and jsonb_typeof(previous)='object'
        and previous->>'schema_version'='analysis.private-evidence.v1'
        and c->>'current_artifact_ref'=p_artifact_id || '@1'
        and c->>'current_source_set_ref'=p_private_evidence->>'source_set_ref'
        and c->>'previous_artifact_ref'=previous->>'projection_of'
        and c->>'previous_source_set_ref'=previous->>'source_set_ref'
        and c->>'previous_artifact_ref'<>c->>'current_artifact_ref'
        and c->>'comparability_state'='COMPARABLE' and c->'reason_codes'='[]'::jsonb
        and jsonb_typeof(c->'change_claims')='array') is not true then
        raise sqlstate '23514' using message='analysis_comparison_binding_invalid'; end if;
      if exists(select 1 from jsonb_array_elements(c->'change_claims') x where
        (x->>'current_ref'=c->>'current_artifact_ref' and x->>'previous_ref'=c->>'previous_artifact_ref'
          and x->>'change_kind' in ('ROUTE_EVIDENCE_CHANGED','ANNOTATION_EVIDENCE_CHANGED',
            'UNKNOWN_SCOPE_CHANGED','CONFLICT_STATE_CHANGED')
          and jsonb_typeof(x->'evidence_refs')='array' and x->'evidence_refs'<>'[]'::jsonb) is not true) then
        raise sqlstate '23514' using message='analysis_comparison_claim_invalid'; end if;
      select coalesce(jsonb_agg(x->'change_kind' order by n),'[]'::jsonb) into changes
        from jsonb_array_elements(c->'change_claims') with ordinality e(x,n);
      if (p_projection->'period_comparison'=jsonb_build_object('state','COMPARABLE',
        'reason_codes','[]'::jsonb,'safe_change_kinds',changes)) is not true then
        raise sqlstate '23514' using message='analysis_comparison_projection_invalid'; end if;
    end if;
  elsif (p_private_evidence->>'schema_version'='analysis.private-evidence.v1'
    and not (p_private_evidence ?| array['comparison_dependency','period_comparison','previous_evidence'])
    and p_projection->'period_comparison'=
      '{"state":"NO_PREVIOUS","reason_codes":[],"safe_change_kinds":[]}'::jsonb) is not true then
    raise sqlstate '23514' using message='analysis_single_period_invalid';
  end if;
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

create or replace function public.analysis_observed_read(
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
      if r.source_guard like 'analysis-db-compare-v1:%' then
        snap := public.analysis_observed_comparison_snapshot(p_user_id,r.period_start,r.period_end,r.report_mode,r.report_type);
      else
        snap := public.analysis_observed_source_snapshot(p_user_id,r.period_start,r.period_end,r.report_mode,r.report_type);
      end if;
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

create or replace function public.analysis_observed_invalidate() returns trigger
language plpgsql security definer set search_path='' set timezone='UTC' as $$
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
      and ((ts at time zone 'UTC' >= case when source_guard like 'analysis-db-compare-v1:%'
          then period_start-(period_end-period_start) else period_start end
          and ts at time zone 'UTC' < period_end)
        or (TG_TABLE_NAME='emotions' and report_type='latest'));
  end loop;
  return null;
end;
$$;
-- CREATE OR REPLACE preserves old RPC ACLs; explicitly close every touched RPC.
revoke all on function public.analysis_observed_comparison_snapshot(uuid,timestamptz,timestamptz,text,text),
  public.analysis_observed_commit(uuid,timestamptz,timestamptz,text,text,text,text,jsonb,jsonb,text),
  public.analysis_observed_read(uuid,text,text,uuid,timestamptz,timestamptz,integer,integer,boolean,integer),
  public.analysis_observed_invalidate() from public,anon,authenticated,service_role;
grant execute on function public.analysis_observed_comparison_snapshot(uuid,timestamptz,timestamptz,text,text),
  public.analysis_observed_commit(uuid,timestamptz,timestamptz,text,text,text,text,jsonb,jsonb,text),
  public.analysis_observed_read(uuid,text,text,uuid,timestamptz,timestamptz,integer,integer,boolean,integer) to service_role;
commit;
