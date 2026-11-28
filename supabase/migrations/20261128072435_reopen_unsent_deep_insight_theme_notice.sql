begin;

create or replace function public.deep_insight_theme_notification_enqueue_due(p_limit integer default 50)
returns jsonb language sql volatile security invoker set search_path='' as $$
  with due as (
    select latest.id,p.id as user_id,j.job_key as prior_job_key,j.status as prior_status,
      j.updated_at as prior_updated_at,j.finished_at as prior_finished_at
    from public.deep_insight_theme_notification_settings pref
    join public.profiles p on p.id=pref.user_id
    cross join lateral (
      select q.id,q.issued_at,q.theme_ready_push_started_at
      from public.deep_insight_questions q where q.user_id=p.id and q.lane='theme'
      order by q.issued_at desc,q.id limit 1
    ) latest
    left join public.astor_jobs j on j.job_key='deep_insight_theme_ready:'||latest.id::text
    where pref.enabled and p.push_enabled is true and nullif(btrim(p.push_token),'') is not null
      and p.push_deep_insight_token_sha256=encode(sha256(convert_to(btrim(p.push_token),'UTF8')),'hex')
      and latest.theme_ready_push_started_at is null
      and latest.issued_at+public.deep_insight_theme_cooldown(p.subscription_tier)<=statement_timestamp()
      and (j.job_key is null or (
        j.job_type='send_fcm_push_v1' and j.user_id=p.id
        and (j.status='done' or (j.status='queued' and j.run_after>statement_timestamp()))
      ))
    order by latest.issued_at,latest.id
    limit least(greatest(coalesce(p_limit,50),1),100)
  ), queued as (
    insert into public.astor_jobs as job(job_key,job_type,user_id,payload,priority,run_after)
    select 'deep_insight_theme_ready:'||id::text,'send_fcm_push_v1',user_id,
      jsonb_build_object('schema_version','fcm.push.job.v1','recipient_mode','user_ids',
        'recipient_user_ids',jsonb_build_array(user_id),'exclude_user_ids','[]'::jsonb,
        'actor_user_id',user_id,'event_type','deep_insight_theme_ready','title','Emlis',
        'body','「わたしを知る問い」で新しいテーマの問いを受け取れます',
        'data',jsonb_build_object('type','deep_insight_theme_ready','target','deep_insight',
          'user_id',user_id,'question_id',id)),5,statement_timestamp()
    from due on conflict(job_key) do update set
      run_after=excluded.run_after,updated_at=statement_timestamp(),status='queued',
      payload=case when job.status='done' then excluded.payload else job.payload end,
      worker_id=case when job.status='done' then null else job.worker_id end,
      started_at=case when job.status='done' then null else job.started_at end,
      finished_at=case when job.status='done' then null else job.finished_at end,
      attempts=case when job.status='done' then 0 else job.attempts end
    where job.job_type=excluded.job_type and job.user_id=excluded.user_id
      and ((job.status='queued' and job.run_after>excluded.run_after)
        or (job.status='done' and exists (
          select 1 from due old where old.prior_job_key=excluded.job_key and old.prior_status='done'
            and old.prior_updated_at is not distinct from job.updated_at
            and old.prior_finished_at is not distinct from job.finished_at
        )))
    returning 1
  )
  select jsonb_build_object('queued',count(*)) from queued;
$$;

revoke all on function public.deep_insight_theme_notification_enqueue_due(integer) from public,anon,authenticated;
grant execute on function public.deep_insight_theme_notification_enqueue_due(integer) to service_role;

commit;
