-- Only newly persisted cumulative maps can schedule background assessment.
-- Their source guard is stable across replays, fresh report IDs and timestamps.
begin;

create function public.deep_insight_record_assessment_enqueue()
returns trigger language plpgsql security invoker set search_path='' as $$
declare
  queued_at timestamptz:=clock_timestamp();
  service_day date:=(queued_at at time zone 'Asia/Tokyo')::date;
begin
  insert into public.astor_jobs as job(job_key,job_type,user_id,payload,priority,run_after,max_attempts,updated_at)
  select 'deep_insight_records_assessment:'||new.user_id::text,'deep_insight_records_assessment_v1',new.user_id,
    jsonb_build_object('source_guard',new.source_guard),30,queued_at,3,queued_at
  from public.profiles p
  where p.id=new.user_id and p.subscription_tier='premium'
    and not exists(select 1 from public.deep_insight_questions q where q.user_id=p.id
      and q.lane='records' and (q.answer_text is null or q.issued_on=service_day))
  on conflict(job_key) do update set
    payload=excluded.payload,
    status=case when job.status='running' then job.status else 'queued' end,
    run_after=case when job.status='running' then job.run_after else excluded.run_after end,
    attempts=case when job.status='running' then job.attempts else 0 end,
    last_error=null,
    updated_at=excluded.updated_at
  where job.payload->>'source_guard' is distinct from excluded.payload->>'source_guard';
  return null;
end;
$$;

create trigger deep_insight_assess_records_after_map
  after insert on public.analysis_observed_artifacts for each row
  when (new.source_profile='cumulative.v1' and new.source_guard ~ '^analysis-db-cumulative-v1:[0-9a-f]{64}$')
  execute function public.deep_insight_record_assessment_enqueue();

-- Settle only the claim that actually ran. A coalesced newer source always
-- receives its own retry budget, even if the previous generation just failed.
create function public.deep_insight_record_assessment_settle(p_job_key text,p_worker_id text,
  p_started_at timestamptz,p_updated_at timestamptz,p_retry boolean)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare settled_at timestamptz:=clock_timestamp();
begin
  update public.astor_jobs job set
    status=case
      when job.updated_at is distinct from p_updated_at then 'queued'
      when p_retry and job.attempts<job.max_attempts then 'queued'
      when p_retry then 'failed'
      else 'done' end,
    attempts=case when job.updated_at is distinct from p_updated_at then 0 else job.attempts end,
    run_after=case when p_retry and job.updated_at=p_updated_at and job.attempts<job.max_attempts
      then settled_at+interval '15 seconds' else settled_at end,
    finished_at=case when job.updated_at is distinct from p_updated_at
      or (p_retry and job.attempts<job.max_attempts) then null else settled_at end,
    last_error=case when p_retry and job.updated_at=p_updated_at
      then 'deep_insight_record_assessment_unavailable' else null end,
    worker_id=null,
    updated_at=settled_at
  where job.job_key=p_job_key and job.job_type='deep_insight_records_assessment_v1'
    and job.status='running' and job.worker_id=p_worker_id and job.started_at=p_started_at;
  return jsonb_build_object('settled',found);
end;
$$;

revoke all on function public.deep_insight_record_assessment_enqueue(),
  public.deep_insight_record_assessment_settle(text,text,timestamptz,timestamptz,boolean)
  from public,anon,authenticated;
grant execute on function public.deep_insight_record_assessment_settle(text,text,timestamptz,timestamptz,boolean)
  to service_role;

commit;
