-- Reuse source-bound questions in the current natural reply for all plans.
-- Based on 20261101010000; preserve natural history/feedback and saved budgets.
begin;
create or replace function public.emlis_thread_commit(
  p_user_id uuid,p_input_id uuid,p_thread_id uuid,p_expected_revision bigint,
  p_source_snapshot jsonb,p_access_tier text,p_next jsonb,p_events jsonb,
  p_finishing_attempt uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare
  parent public.emotions; prior public.emlis_input_threads;
  tier text; v jsonb; n bigint; questions integer; instant timestamptz; started_limit integer; native_questions boolean; h public.emotions; ht public.emlis_input_threads; g jsonb; f jsonb;
begin
  select * into parent from public.emotions where id=p_input_id and user_id=p_user_id for share;
  if not found then raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  select subscription_tier into tier from public.profiles where id=p_user_id for update;
  tier := coalesce(tier,'free');
  select * into prior from public.emlis_input_threads where original_emotion_id=p_input_id for update;
  instant := clock_timestamp();
  if not public.emlis_parent_visible(parent.created_at,tier,instant) then
    raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  if public.emlis_parent_source(parent) is distinct from p_source_snapshot or tier <> p_access_tier then
    raise sqlstate '40001' using message='emlis_source_or_access_changed'; end if;
  if (prior.id is not null and (prior.id<>p_thread_id or prior.user_id<>p_user_id or prior.revision<>p_expected_revision))
    or (prior.id is null and p_expected_revision<>0) then
    raise sqlstate '40001' using message='emlis_revision_conflict'; end if;
  if prior.id is not null and prior.source_snapshot is distinct from p_source_snapshot then
    raise sqlstate '40001' using message='emlis_source_changed'; end if;
  if p_finishing_attempt is not null and (prior.active_attempt_id is distinct from p_finishing_attempt
    or prior.processing_deadline_at is null or prior.processing_deadline_at <= instant) then
    raise sqlstate '40001' using message='emlis_attempt_stale'; end if;
  if p_finishing_attempt is null and prior.active_attempt_id is not null then
    raise sqlstate '40001' using message='emlis_attempt_active'; end if;
  select count(*) into questions from jsonb_array_elements(p_events) x where x->>'kind'='QUESTION';
  if (p_next->>'issued_count')::integer <> coalesce(prior.issued_count,0)+questions then
    raise sqlstate '23514' using message='emlis_issuance_count_invalid'; end if;
  -- The policy is established only when a new natural thread is created.
  -- Existing Q2/Q3/natural threads keep their original budget and policy.
  if prior.id is not null and
      (prior.data->>'natural_question_policy') is distinct from
      (p_next->'data'->>'natural_question_policy') then
    raise sqlstate '23514' using message='emlis_natural_question_policy_immutable'; end if;
  native_questions := coalesce(
    p_next->'data'->>'runtime_profile' = 'q3.plan.sequential.v1'
    and p_next->'data'->>'response_profile' = 'natural_reply.v1'
    and p_next->'data'->>'natural_question_policy' = 'native_bound_question.v1', false);
  if p_next->'data' ? 'natural_question_policy' and not native_questions then
    raise sqlstate '23514' using message='emlis_natural_question_policy_invalid'; end if;
  started_limit := case when prior.id is not null then prior.started_question_limit
    when native_questions then 3
    when p_next->'data'->>'runtime_profile' = 'q3.plan.sequential.v1' and tier = 'premium' then 3 else 1 end;
  if coalesce((p_next->>'started_question_limit')::integer,1) <> started_limit then
    raise sqlstate '23514' using message='emlis_started_limit_immutable'; end if;
  if questions > 1 or (questions > 0 and (p_next->>'issued_count')::integer >
      least(started_limit,case when native_questions or tier='premium' then 3 else 1 end)) then
    raise sqlstate '23514' using message='emlis_question_budget_exhausted'; end if;
  for v in select value from jsonb_array_elements(p_events) loop
    if v->>'kind'='QUESTION' and (v->>'round_index')::integer <> coalesce(prior.issued_count,0)+1 then
      raise sqlstate '23514' using message='emlis_question_round_invalid'; end if;
    if v->>'kind'='ANSWER' and not exists(select 1 from public.emlis_thread_events q
      where q.thread_id=p_thread_id and q.kind='QUESTION' and q.question_id=v->>'question_id'
        and q.round_index=(v->>'round_index')::integer and q.round_index=prior.issued_count) then
      raise sqlstate '23514' using message='emlis_answer_round_invalid'; end if;
  end loop;
  if p_next->'data'->>'runtime_profile'='q3.plan.sequential.v1' and (exists(select 1 from jsonb_array_elements(p_events) x where x->>'kind' in ('MEANING_UPDATE','OBSERVATION','QUESTION')) or p_next->'data' ? 'frame_feedback_write' or p_next->'data'->>'body_state'='UNCHANGED') then
    if jsonb_array_length(coalesce(p_next->'data'->'context_guards','[]')) > (case when tier='premium' then 6 when tier='plus' then 3 else 0 end) then
      raise sqlstate '40001' using message='emlis_context_access_changed'; end if;
    for g in select value from jsonb_array_elements(coalesce(p_next->'data'->'context_guards','[]')) order by value->>0 loop
      select * into h from public.emotions where id=(g->>0)::uuid and user_id=p_user_id for share;
      if not found or h.id=p_input_id or (h.created_at,h.id)>=(parent.created_at,parent.id)
        or not public.emlis_parent_visible(h.created_at,tier,instant)
        or (p_next->'data'->>'response_profile' is distinct from 'natural_reply.v1' and h.created_at < instant at time zone 'UTC' - (case when tier='premium' then interval '3650 days' else interval '365 days' end))
        or md5(public.emlis_parent_source(h)::text) <> g->>1 then
        raise sqlstate '40001' using message='emlis_context_source_changed'; end if;
      select * into ht from public.emlis_input_threads where original_emotion_id=h.id for share;
      if coalesce(ht.revision,0) <> (g->>2)::bigint then
        raise sqlstate '40001' using message='emlis_context_meaning_changed'; end if;
    end loop;
    if p_next->'data'->'context_feedback' is distinct from coalesce((select jsonb_agg(jsonb_build_array(x.frame_key,x.version) order by x.frame_key)
      from public.emlis_frame_feedback x where x.user_id=p_user_id and tier='premium'
        and (p_next->'data'->>'response_profile' is distinct from 'natural_reply.v1'
          or x.source_emotion_id=p_input_id or x.source_emotion_id in
            (select (guard_row.value->>0)::uuid from jsonb_array_elements(coalesce(p_next->'data'->'context_guards','[]')) as guard_row(value)))),'[]'::jsonb) then
      raise sqlstate '40001' using message='emlis_frame_feedback_changed'; end if;
    f := p_next->'data'->'frame_feedback_write';
    if f is not null and f<>'null'::jsonb then
      if tier<>'premium' or not exists(select 1 from public.emotions e where e.id=(f->>'source_emotion_id')::uuid and e.user_id=p_user_id) then
        raise sqlstate '40001' using message='emlis_frame_owner_changed'; end if;
      insert into public.emlis_frame_feedback(user_id,source_emotion_id,frame_key,frame_ref,status,correction_text)
        values(p_user_id,(f->>'source_emotion_id')::uuid,f->>'frame_key',f->>'frame_ref',f->>'status',f->>'correction_text')
      on conflict(user_id,frame_key) do update set frame_ref=excluded.frame_ref,status=excluded.status,
        correction_text=excluded.correction_text,version=public.emlis_frame_feedback.version+1,updated_at=instant;
    end if;
  end if;
  if prior.id is null then
    insert into public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data,started_question_limit)
      values(p_thread_id,p_user_id,p_input_id,1,'COMPLETED',0,p_source_snapshot,'{}',started_limit);
  end if;
  select coalesce(max(seq),0) into n from public.emlis_thread_events where thread_id=p_thread_id;
  for v in select value from jsonb_array_elements(p_events) loop
    n:=n+1;
    insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,operation_id,attempt_id,idempotency_key,payload)
      values((v->>'id')::uuid,p_thread_id,n,v->>'kind',(v->>'round_index')::integer,
        v->>'question_id',(v->>'operation_id')::uuid,(v->>'attempt_id')::uuid,v->>'idempotency_key',v->'payload');
  end loop;
  update public.emlis_input_threads set revision=p_expected_revision+1,state=p_next->>'state',
    issued_count=(p_next->>'issued_count')::integer,
    current_meaning_event_id=(p_next->>'current_meaning_event_id')::uuid,
    last_observation_event_id=(p_next->>'last_observation_event_id')::uuid,
    latest_answer_event_id=(p_next->>'latest_answer_event_id')::uuid,
    source_prefix_ref=p_next->>'source_prefix_ref',evaluated_prefix_ref=p_next->>'evaluated_prefix_ref',
    active_operation_id=(p_next->>'active_operation_id')::uuid,
    active_attempt_id=(p_next->>'active_attempt_id')::uuid,
    processing_deadline_at=(p_next->>'processing_deadline_at')::timestamptz,
    data=(p_next->'data')-'frame_feedback_write',updated_at=instant where id=p_thread_id;
  return public.emlis_thread_read(p_user_id,p_input_id,null);
end;
$$;
revoke all on function public.emlis_thread_commit(uuid,uuid,uuid,bigint,jsonb,text,jsonb,jsonb,uuid) from public,anon,authenticated;
grant execute on function public.emlis_thread_commit(uuid,uuid,uuid,bigint,jsonb,text,jsonb,jsonb,uuid) to service_role;
commit;

