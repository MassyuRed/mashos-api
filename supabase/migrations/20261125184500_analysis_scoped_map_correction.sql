-- Confirm that a correction selected from a scoped map was authorized under
-- the same viewing plan that is current in the save transaction.
begin;

alter function public.analysis_map_correction_submit(uuid,text,text,text,text,text,text,text)
  rename to analysis_map_correction_submit_original_field;
revoke all on function public.analysis_map_correction_submit_original_field(uuid,text,text,text,text,text,text,text)
  from public,anon,authenticated,service_role;

create function public.analysis_map_correction_submit(
  p_user_id uuid,p_artifact_ref text,p_kind text,p_ref text,p_field text,
  p_target_text text,p_explanation text,p_idempotency_key text,p_visible_tier text default null)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare tier text; axes jsonb; scoped boolean;
begin
  -- Use the same owner lock and table order as existing map correction writes.
  perform 1 from auth.users where id=p_user_id for update nowait;
  if not found then raise sqlstate 'P0002' using message='analysis_owner_unavailable'; end if;
  if not exists(select 1 from public.analysis_map_interpretation_corrections
      where user_id=p_user_id and idempotency_key=p_idempotency_key) then
    lock table public.emotions,public.profiles,public.emlis_input_threads,public.emlis_thread_events,
      public.analysis_observed_artifacts in share mode nowait;
    select safe_projection#>'{overview,primary_structures}' into axes
      from public.analysis_observed_artifacts where user_id=p_user_id
        and artifact_id || '@' || artifact_version::text=p_artifact_ref and source_profile='cumulative.v1';
    scoped:=case when jsonb_typeof(axes)='array' then jsonb_array_length(axes)=0
      or exists(select 1 from jsonb_array_elements(axes) axis where axis ? 'criterion') else false end;
    if scoped then
      select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
      if p_visible_tier is null then
        raise sqlstate 'P0002' using message='analysis_map_correction_target_unavailable'; end if;
      if tier is null or tier not in ('free','plus','premium') or tier is distinct from p_visible_tier then
        raise sqlstate '40001' using message='analysis_map_correction_plan_changed'; end if;
    end if;
  end if;
  return public.analysis_map_correction_submit_original_field(p_user_id,p_artifact_ref,p_kind,p_ref,p_field,
    p_target_text,p_explanation,p_idempotency_key);
exception when lock_not_available or deadlock_detected then
  raise sqlstate '40001' using message='analysis_map_correction_source_busy';
end;
$$;

revoke all on function public.analysis_map_correction_submit(uuid,text,text,text,text,text,text,text,text)
  from public,anon,authenticated;
grant execute on function public.analysis_map_correction_submit(uuid,text,text,text,text,text,text,text,text)
  to service_role;

commit;
