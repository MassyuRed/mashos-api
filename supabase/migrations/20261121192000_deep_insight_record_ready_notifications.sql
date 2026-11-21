-- A grounded reflection is saved and its owner-only notification is queued
-- in the same transaction. The notification does not carry the question text.
begin;

alter table public.deep_insight_questions add column record_ready_push_started_at timestamptz;
grant update(record_ready_push_started_at) on public.deep_insight_questions to service_role;

create function public.deep_insight_record_notification_enqueue()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
  insert into public.astor_jobs(job_key,job_type,user_id,payload,priority,run_after)
  select 'deep_insight_record_ready:'||new.id::text,'send_fcm_push_v1',new.user_id,
    jsonb_build_object('schema_version','fcm.push.job.v1','recipient_mode','user_ids',
      'recipient_user_ids',jsonb_build_array(new.user_id),'exclude_user_ids','[]'::jsonb,
      'actor_user_id',new.user_id,'event_type','deep_insight_record_ready','title','Emlis',
      'body','「わたしを知る問い」に新しいふりかえりの問いが届きました',
      'data',jsonb_build_object('type','deep_insight_record_ready','target','deep_insight',
        'user_id',new.user_id,'question_id',new.id)),5,clock_timestamp()
  from public.profiles p
  where p.id=new.user_id and p.subscription_tier='premium' and p.push_enabled is true
    and nullif(btrim(p.push_token),'') is not null
  on conflict(job_key) do nothing;
  return null;
end;
$$;

create trigger deep_insight_record_ready
  after update of grounding_receipt on public.deep_insight_questions for each row
  when (new.lane='records' and old.grounding_receipt is null and new.grounding_receipt is not null)
  execute function public.deep_insight_record_notification_enqueue();

create function public.deep_insight_record_notification_can_send(p_user_id uuid,p_question_id uuid)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
begin
  update public.deep_insight_questions q set record_ready_push_started_at=clock_timestamp()
    from public.profiles p
    where p.id=q.user_id and q.user_id=p_user_id and q.id=p_question_id and q.lane='records'
      and q.grounding_receipt is not null and q.answer_text is null and q.record_ready_push_started_at is null
      and p.subscription_tier='premium' and p.push_enabled is true
      and nullif(btrim(p.push_token),'') is not null;
  return jsonb_build_object('eligible',found);
end;
$$;

revoke all on function public.deep_insight_record_notification_enqueue(),
  public.deep_insight_record_notification_can_send(uuid,uuid) from public,anon,authenticated;
grant execute on function public.deep_insight_record_notification_can_send(uuid,uuid) to service_role;

commit;
