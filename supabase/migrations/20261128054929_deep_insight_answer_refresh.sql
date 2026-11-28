begin;

-- Keep the verified answer and its existing cumulative-map job in one
-- transaction. The previous RPC remains available to older API deployments.
create function public.deep_insight_answer_and_refresh(
  p_user_id uuid, p_question_id uuid, p_answer_text text, p_enqueue_map boolean
) returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  saved jsonb;
  queued_at timestamptz;
begin
  saved := public.deep_insight_answer(p_user_id, p_question_id, p_answer_text);
  if p_enqueue_map is not true or saved->'inserted' is distinct from 'true'::jsonb then
    return saved;
  end if;

  queued_at := clock_timestamp();
  insert into public.astor_jobs as job(job_key,job_type,user_id,payload,status,priority,run_after,
    attempts,max_attempts,updated_at)
  values('myprofile_latest_refresh:'||p_user_id::text,'myprofile_latest_refresh_v1',p_user_id,
    jsonb_build_object('trigger','deep_insight_answer','force',false,'requested_at',queued_at),
    'queued',50,queued_at+interval '20 seconds',0,8,queued_at)
  on conflict(job_key) do update set
    payload=case when job.status in ('queued','running') and job.payload->'force'='true'::jsonb
      then excluded.payload||'{"force":true}'::jsonb else excluded.payload end,
    status=case when job.status='running' then job.status else excluded.status end,
    run_after=case
      when job.status='running' then job.run_after
      when job.status='queued' then greatest(job.run_after,excluded.run_after)
      else excluded.run_after end,
    attempts=case when job.status in ('queued','running') then job.attempts else excluded.attempts end,
    max_attempts=case when job.status in ('queued','running') then job.max_attempts else excluded.max_attempts end,
    priority=greatest(job.priority,excluded.priority),
    last_error=case
      when job.status='running' then 'map_updated_while_running'
      when job.status='queued' then job.last_error
      else null end,
    worker_id=case when job.status='running' then job.worker_id else null end,
    started_at=case when job.status='running' then job.started_at else null end,
    finished_at=null,
    updated_at=excluded.updated_at
  where job.user_id=excluded.user_id and job.job_type=excluded.job_type
    and job.status in ('queued','running','done','failed');
  if not found then
    raise exception 'deep_insight_map_queue_unavailable';
  end if;
  return saved;
end;
$$;

revoke all on function public.deep_insight_answer_and_refresh(uuid,uuid,text,boolean)
  from public,anon,authenticated;
grant execute on function public.deep_insight_answer_and_refresh(uuid,uuid,text,boolean) to service_role;

commit;
