-- Private opt-in for notifying the owner when the next theme question is available.
begin;

create table public.deep_insight_theme_notification_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default false
);
alter table public.deep_insight_theme_notification_settings enable row level security;
revoke all on public.deep_insight_theme_notification_settings from public,anon,authenticated,service_role;
grant select,insert,update on public.deep_insight_theme_notification_settings to service_role;

-- A recovered worker must not repeat an external send whose outcome is unknown.
alter table public.deep_insight_questions add column theme_ready_push_started_at timestamptz;
grant update (theme_ready_push_started_at) on public.deep_insight_questions to service_role;

create function public.deep_insight_theme_notification_read(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  select jsonb_build_object('enabled',coalesce((
    select enabled from public.deep_insight_theme_notification_settings where user_id=p_user_id
  ),false));
$$;

create function public.deep_insight_theme_notification_write(p_user_id uuid,p_enabled boolean)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
begin
  if p_user_id is null or p_enabled is null then
    raise sqlstate '22023' using message='deep_insight_theme_notification_invalid';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('deep-insight:' || p_user_id::text,0));
  insert into public.deep_insight_theme_notification_settings(user_id,enabled)
  values(p_user_id,p_enabled)
  on conflict(user_id) do update set enabled=excluded.enabled;
  return jsonb_build_object('enabled',p_enabled);
end;
$$;

create or replace function public.deep_insight_state(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  select public.deep_insight_state_at(p_user_id,statement_timestamp())
    || jsonb_build_object('theme_notification_enabled',
      public.deep_insight_theme_notification_read(p_user_id)->'enabled');
$$;

create function public.deep_insight_theme_notification_enqueue_due(p_limit integer default 50)
returns jsonb language sql volatile security invoker set search_path='' as $$
  with due as (
    select latest.id,p.id as user_id
    from public.deep_insight_theme_notification_settings pref
    join public.profiles p on p.id=pref.user_id
    cross join lateral (
      select q.id,q.issued_at,q.theme_ready_push_started_at
      from public.deep_insight_questions q where q.user_id=p.id and q.lane='theme'
      order by q.issued_at desc,q.id limit 1
    ) latest
    where pref.enabled and p.push_enabled is true and nullif(btrim(p.push_token),'') is not null
      and latest.theme_ready_push_started_at is null
      and latest.issued_at+public.deep_insight_theme_cooldown(p.subscription_tier)<=statement_timestamp()
      and not exists (
        select 1 from public.astor_jobs j where j.job_key='deep_insight_theme_ready:'||latest.id::text
          and (j.status<>'queued' or j.run_after<=statement_timestamp())
      )
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
      run_after=excluded.run_after,updated_at=statement_timestamp()
    where job.status='queued' and job.run_after>excluded.run_after
    returning 1
  )
  select jsonb_build_object('queued',count(*)) from queued;
$$;

-- Claim the one send attempt immediately before FCM. The lock is shared with
-- issuance and opt-in edits, so a newer question or disabled setting wins.
create function public.deep_insight_theme_notification_can_send(p_user_id uuid,p_question_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  checked_at timestamptz;
  available_at timestamptz;
begin
  if p_user_id is null or p_question_id is null then
    return jsonb_build_object('eligible',false);
  end if;
  perform pg_advisory_xact_lock(hashtextextended('deep-insight:' || p_user_id::text,0));
  checked_at:=clock_timestamp();
  select q.issued_at+public.deep_insight_theme_cooldown(p.subscription_tier) into available_at
  from public.deep_insight_questions q
  join public.profiles p on p.id=q.user_id
  join public.deep_insight_theme_notification_settings pref on pref.user_id=p.id
  where q.id=p_question_id and q.user_id=p_user_id and q.lane='theme'
    and q.theme_ready_push_started_at is null and pref.enabled and p.push_enabled is true
    and nullif(btrim(p.push_token),'') is not null
    and q.id=(
      select latest.id from public.deep_insight_questions latest
      where latest.user_id=p_user_id and latest.lane='theme'
      order by latest.issued_at desc,latest.id limit 1
    );
  if available_at is null then
    return jsonb_build_object('eligible',false);
  end if;
  if available_at>checked_at then
    return jsonb_build_object('eligible',false,'defer_until',available_at);
  end if;
  update public.deep_insight_questions set theme_ready_push_started_at=checked_at
    where id=p_question_id and user_id=p_user_id and theme_ready_push_started_at is null;
  return jsonb_build_object('eligible',found);
end;
$$;

revoke all on function public.deep_insight_theme_notification_read(uuid),
  public.deep_insight_theme_notification_write(uuid,boolean),
  public.deep_insight_theme_notification_enqueue_due(integer),
  public.deep_insight_theme_notification_can_send(uuid,uuid) from public,anon,authenticated;
grant execute on function public.deep_insight_theme_notification_read(uuid),
  public.deep_insight_theme_notification_write(uuid,boolean),
  public.deep_insight_theme_notification_enqueue_due(integer),
  public.deep_insight_theme_notification_can_send(uuid,uuid) to service_role;

commit;
