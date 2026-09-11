-- Q3 extends saved Q2 threads without changing their source/profile or starting budget.
begin;
alter table public.emlis_input_threads
  add column started_question_limit integer not null default 1 check (started_question_limit in (1,3));
alter table public.emlis_input_threads drop constraint emlis_input_threads_state_check;
alter table public.emlis_input_threads add constraint emlis_input_threads_state_check
  check (state in ('INITIALIZING','AWAITING_ANSWER','AWAITING_CONTINUE','REFINING','COMPLETED','RESPONSE_FAILED'));
alter table public.emlis_input_threads drop constraint emlis_input_threads_issued_count_check;
alter table public.emlis_input_threads add constraint emlis_input_threads_issued_count_check check (issued_count between 0 and 3);
alter table public.emlis_thread_events drop constraint emlis_thread_events_round_index_check;
alter table public.emlis_thread_events add constraint emlis_thread_events_round_index_check check (round_index between 0 and 3);
create unique index emlis_question_identity_once on public.emlis_thread_events(thread_id,question_id) where kind='QUESTION';
create table public.emlis_frame_feedback (
  user_id uuid not null references auth.users(id) on delete cascade,
  source_emotion_id uuid not null references public.emotions(id) on delete cascade,
  frame_key text not null,
  frame_ref text not null,
  status text not null check(status in ('CONFIRMED','REJECTED','REVISED')),
  correction_text text,
  version bigint not null default 1,
  updated_at timestamptz not null default clock_timestamp(),
  primary key(user_id,frame_key),
  check((status='REVISED') = (correction_text is not null))
);
alter table public.emlis_frame_feedback enable row level security;
revoke all on public.emlis_frame_feedback from public,anon,authenticated;
grant select,insert,update,delete on public.emlis_frame_feedback to service_role;

create function public.emlis_thread_context(p_user_id uuid,p_input_id uuid) returns jsonb
language sql volatile security invoker set search_path='' as $$
  select jsonb_build_object('history',coalesce((select jsonb_agg(x.row order by x.created_at desc,x.id) from (
    select h.created_at,h.id,jsonb_build_object('original',public.emlis_parent_source(h),
      'thread',case when ht.id is null then null else to_jsonb(ht)-'source_snapshot' end,
      'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq) from public.emlis_thread_events v
        where v.thread_id=ht.id and v.kind in ('QUESTION','ANSWER')),'[]'::jsonb),
      'guard',jsonb_build_array(h.id,md5(public.emlis_parent_source(h)::text),coalesce(ht.revision,0))) as row
    from public.emotions h left join public.emlis_input_threads ht on ht.original_emotion_id=h.id
    where h.user_id=p_user_id and (ht.id is null or ht.user_id=p_user_id) and h.id<>e.id
      and (h.created_at,h.id)<(e.created_at,e.id)
      and p.subscription_tier in ('plus','premium')
      and public.emlis_parent_visible(h.created_at,p.subscription_tier,statement_timestamp())
      and h.created_at >= statement_timestamp() at time zone 'UTC' -
          case when p.subscription_tier='premium' then interval '3650 days' else interval '365 days' end
      and (ht.latest_answer_event_id is null or (ht.source_prefix_ref=ht.evaluated_prefix_ref
           and ht.data->>'answer_assessment'='RESOLVED'))
    order by h.created_at desc,h.id limit case when p.subscription_tier='premium' then 6 else 3 end
  )x),'[]'::jsonb),'feedback',coalesce((select jsonb_agg(to_jsonb(f) order by f.frame_key)
       from public.emlis_frame_feedback f where f.user_id=p_user_id and p.subscription_tier='premium'),'[]'::jsonb))
  from public.emotions e join public.profiles p on p.id=e.user_id where e.id=p_input_id and e.user_id=p_user_id
    and public.emlis_parent_visible(e.created_at,p.subscription_tier,statement_timestamp());
$$;
revoke all on function public.emlis_thread_context(uuid,uuid) from public,anon,authenticated;
grant execute on function public.emlis_thread_context(uuid,uuid) to service_role;

create or replace function public.emlis_thread_commit(
  p_user_id uuid,p_input_id uuid,p_thread_id uuid,p_expected_revision bigint,
  p_source_snapshot jsonb,p_access_tier text,p_next jsonb,p_events jsonb,
  p_finishing_attempt uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare
  parent public.emotions; prior public.emlis_input_threads;
  tier text; v jsonb; n bigint; questions integer; instant timestamptz; started_limit integer; h public.emotions; ht public.emlis_input_threads; g jsonb; f jsonb;
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
  started_limit := case when prior.id is not null then prior.started_question_limit
    when p_next->'data'->>'runtime_profile' = 'q3.plan.sequential.v1' and tier = 'premium' then 3 else 1 end;
  if coalesce((p_next->>'started_question_limit')::integer,1) <> started_limit then
    raise sqlstate '23514' using message='emlis_started_limit_immutable'; end if;
  if questions > 1 or (questions > 0 and (p_next->>'issued_count')::integer >
      least(started_limit,case when tier='premium' then 3 else 1 end)) then
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
        or h.created_at < instant at time zone 'UTC' - (case when tier='premium' then interval '3650 days' else interval '365 days' end)
        or md5(public.emlis_parent_source(h)::text) <> g->>1 then
        raise sqlstate '40001' using message='emlis_context_source_changed'; end if;
      select * into ht from public.emlis_input_threads where original_emotion_id=h.id for share;
      if coalesce(ht.revision,0) <> (g->>2)::bigint then
        raise sqlstate '40001' using message='emlis_context_meaning_changed'; end if;
    end loop;
    if p_next->'data'->'context_feedback' is distinct from coalesce((select jsonb_agg(jsonb_build_array(x.frame_key,x.version) order by x.frame_key)
      from public.emlis_frame_feedback x where x.user_id=p_user_id and tier='premium'),'[]'::jsonb) then
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
commit;
