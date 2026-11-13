-- Exact saved frame targets across threads; no new tables, columns or public signatures.
-- Carry only user-authored correction sources into entitled natural history.
-- Search all entitled prior records; the model still receives at most 3/6.
-- Saved replies reread their exact selected IDs rather than searching again.
begin;
create or replace function public.emlis_thread_related_context(
  p_user_id uuid,p_input_id uuid,p_context_guards jsonb default null
) returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  parent public.emotions; current_thread public.emlis_input_threads;
  tier text; instant timestamptz := clock_timestamp(); selected_limit integer;
  focus text; history jsonb; feedback jsonb; target_dependencies jsonb;
begin
  select * into parent from public.emotions where id=p_input_id and user_id=p_user_id;
  if not found then raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  tier := coalesce(tier,'free');
  if not public.emlis_parent_visible(parent.created_at,tier,instant) then
    raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  select * into current_thread from public.emlis_input_threads where original_emotion_id=p_input_id;
  if current_thread.id is not null and current_thread.user_id<>p_user_id then
    raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  selected_limit := case tier when 'premium' then 6 when 'plus' then 3 else 0 end;
  if p_context_guards is not null then
    if jsonb_typeof(p_context_guards) is distinct from 'array' then
      raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
    if jsonb_array_length(p_context_guards)>6 or exists(
      select 1 from jsonb_array_elements(p_context_guards) g
      where case when jsonb_typeof(g)<>'array' then true else jsonb_array_length(g)<>3 end
    ) then raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
    if exists(select 1 from jsonb_array_elements(p_context_guards) g
      where jsonb_typeof(g->0)<>'string' or jsonb_typeof(g->1)<>'string'
        or jsonb_typeof(g->2)<>'number' or coalesce(g->>1,'') !~ '^[0-9a-f]{32}$'
        or coalesce(g->>2,'') !~ '^[0-9]+$') then
      raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
    if (select count(distinct (g->>0)::uuid) from jsonb_array_elements(p_context_guards) g)
      <> jsonb_array_length(p_context_guards) then
      raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
  end if;
  if selected_limit=0 then
    return jsonb_build_object('history','[]'::jsonb,'feedback','[]'::jsonb,'frame_target_dependencies','[]'::jsonb); end if;
  select concat_ws(E'\n',parent.memo,parent.memo_action,
    (select string_agg(v.payload->'source'->>'answer_text_private',E'\n' order by v.seq)
      from public.emlis_thread_events v where v.thread_id=current_thread.id and v.kind='ANSWER'),
    (select string_agg(v.payload->'source'->>'explanation',E'\n' order by v.seq)
      from public.emlis_thread_events v where v.thread_id=current_thread.id
        and v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'),
    (select string_agg(f.correction_text,E'\n' order by f.updated_at,f.frame_key)
      from public.emlis_frame_feedback f where f.user_id=p_user_id
        and f.source_emotion_id=parent.id and f.status='REVISED')) into focus;
  with segments as (
    select (regexp_matches(lower(coalesce(focus,'')), '[0-9a-z一-龯ぁ-んァ-ヶー]+','g'))[1] segment
  ), terms as (
    select distinct substring(s.segment from g.n for 3) term from segments s
      cross join lateral generate_series(1,char_length(s.segment)-2) g(n)
    union select segment from segments where char_length(segment)=2
  ), eligible as (
    select h.id,h.created_at,lower(concat_ws(E'\n',h.memo,h.memo_action,
      (select string_agg(v.payload->'source'->>'answer_text_private',E'\n' order by v.seq)
        from public.emlis_thread_events v where v.thread_id=ht.id and v.kind='ANSWER'),
    (select string_agg(v.payload->'source'->>'explanation',E'\n' order by v.seq)
      from public.emlis_thread_events v where v.thread_id=ht.id
        and v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'),
      (select string_agg(f.correction_text,E'\n' order by f.updated_at,f.frame_key)
        from public.emlis_frame_feedback f where f.user_id=p_user_id
          and f.source_emotion_id=h.id and f.status='REVISED'))) search_text
    from public.emotions h left join public.emlis_input_threads ht on ht.original_emotion_id=h.id
    where h.user_id=p_user_id and (ht.id is null or ht.user_id=p_user_id)
      and (ht.id is null or ht.source_snapshot=public.emlis_parent_source(h))
      and (h.created_at,h.id)<(parent.created_at,parent.id)
      and public.emlis_parent_visible(h.created_at,tier,instant)
      and (p_context_guards is null or h.id in
        (select (g->>0)::uuid from jsonb_array_elements(p_context_guards) g))
  ), ranked as (
    select e.id,e.created_at,case when p_context_guards is not null then 1
      else (select count(*) from terms q where strpos(e.search_text,q.term)>0) end score from eligible e
  ), chosen as (
    select * from ranked where p_context_guards is not null or score>0
    order by score desc,created_at desc,id limit selected_limit
  )
  select coalesce(jsonb_agg(x.payload order by x.created_at,x.id),'[]'::jsonb) into history from (
    select h.id,h.created_at,jsonb_build_object('original',public.emlis_parent_source(h),
      'thread',case when ht.id is null then null else to_jsonb(ht)-'source_snapshot' end,
      'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq) from public.emlis_thread_events v
        where v.thread_id=ht.id and (v.kind in ('QUESTION','ANSWER') or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'))),'[]'::jsonb),
      'guard',jsonb_build_array(h.id,md5(public.emlis_parent_source(h)::text),coalesce(ht.revision,0))) payload
    from chosen c join public.emotions h on h.id=c.id
      left join public.emlis_input_threads ht on ht.original_emotion_id=h.id
  ) x;
  -- Only the displayed target travels from its owning thread. The owning
  -- record's body/events do not become another admitted history record.
  select coalesce(jsonb_agg(to_jsonb(f)||jsonb_build_object('target_operations',
    coalesce(targets.operations,'[]'::jsonb)) order by f.frame_key),'[]'::jsonb) into feedback
  from public.emlis_frame_feedback f
  left join lateral (
    select jsonb_agg(candidate.operation order by candidate.id) operations from (
      select v.id,jsonb_build_object('id',v.id,'kind',v.kind,'payload',v.payload,
        'origin_guard',jsonb_build_array(b.id,md5(public.emlis_parent_source(b)::text),
          v.id,md5(v.payload::text))) operation
      from public.emlis_thread_events v
      join public.emlis_input_threads bt on bt.id=v.thread_id and bt.user_id=p_user_id
      join public.emotions b on b.id=bt.original_emotion_id and b.user_id=p_user_id
      where v.kind='OPERATION' and v.payload->>'status'='FRAME_'||f.status
        and bt.data->>'runtime_profile'='q3.plan.sequential.v1'
        and bt.data->>'response_profile'='natural_reply.v1'
        and bt.source_snapshot=public.emlis_parent_source(b)
        and public.emlis_parent_visible(b.created_at,tier,instant)
        and v.payload->'frame_feedback_target'->>'frame_key'=f.frame_key
        and v.payload->'frame_feedback_target'->>'frame_ref'=f.frame_ref
        and v.payload->'frame_feedback_target'->>'input_id'=f.source_emotion_id::text
        and v.payload->'frame_feedback_target'->'feedback_version'=to_jsonb(f.version)
        and f.version>1
      order by v.id limit 2
    ) candidate
  ) targets on true
  where f.user_id=p_user_id and tier='premium'
    and (f.source_emotion_id=parent.id or f.source_emotion_id in
      (select (h->'original'->>'id')::uuid from jsonb_array_elements(history) h));
  select coalesce(jsonb_agg(jsonb_build_array(f->>'frame_key',f->'version',
    op->'origin_guard'->0,op->'origin_guard'->1,op->'origin_guard'->2,op->'origin_guard'->3)
    order by f->>'frame_key'),'[]'::jsonb) into target_dependencies
    from jsonb_array_elements(feedback) f
    cross join lateral jsonb_array_elements(f->'target_operations') op
    where jsonb_array_length(f->'target_operations')=1
      and op->'origin_guard'->>0<>parent.id::text;
  return jsonb_build_object('history',history,'feedback',feedback,
    'frame_target_dependencies',target_dependencies);
end;
$$;
revoke all on function public.emlis_thread_related_context(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.emlis_thread_related_context(uuid,uuid,jsonb) to service_role;



-- Reuse source-bound questions in the current natural reply for all plans.
-- Based on 20261101010000; preserve natural history/feedback and saved budgets.

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
  if p_next->'data'->>'runtime_profile'='q3.plan.sequential.v1' and (exists(select 1 from jsonb_array_elements(p_events) x where x->>'kind' in ('MEANING_UPDATE','OBSERVATION','QUESTION')) or p_next->'data' ? 'frame_feedback_write' or p_next->'data'->>'body_state'='UNCHANGED'
      or (native_questions and p_next->'data'->>'body_state'='REFINED' and exists(
        select 1 from jsonb_array_elements(p_events) x where x->>'kind'='TERMINAL' and x->'payload'->>'reason'='stop'))) or (p_next->'data' ? 'frame_target_dependencies' and exists(
        select 1 from jsonb_array_elements(p_events) x where x->>'kind' in ('MEANING_UPDATE','OBSERVATION','QUESTION','ANSWER','TERMINAL')
          or x->'payload'->>'status'='RUNNING'
          or x->'payload'->>'stage' in ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED','INTERPRETATION_CORRECTION'))) then
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
  if p_next->'data' ? 'frame_target_dependencies' and (
      exists(select 1 from jsonb_array_elements(p_events) x where x->>'kind' in ('MEANING_UPDATE','OBSERVATION','QUESTION','ANSWER','TERMINAL')
        or x->'payload'->>'status'='RUNNING'
        or x->'payload'->>'stage' in ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED','INTERPRETATION_CORRECTION'))
      or p_next->'data' ? 'frame_feedback_write') then
    if jsonb_typeof(p_next->'data'->'frame_target_dependencies') is distinct from 'array' then
      raise sqlstate '40001' using message='emlis_frame_target_changed'; end if;
    for g in select value from jsonb_array_elements(p_next->'data'->'frame_target_dependencies') order by value->>2,value->>4 loop
      if jsonb_typeof(g) is distinct from 'array' or jsonb_array_length(g)<>6 then
        raise sqlstate '40001' using message='emlis_frame_target_changed'; end if;
      perform 1 from public.emotions b
        join public.emlis_input_threads bt on bt.original_emotion_id=b.id and bt.user_id=p_user_id
        join public.emlis_thread_events v on v.thread_id=bt.id and v.id=(g->>4)::uuid
        where b.id=(g->>2)::uuid and b.user_id=p_user_id
          and md5(public.emlis_parent_source(b)::text)=g->>3 and md5(v.payload::text)=g->>5
        for share of b,bt,v;
      if not found then raise sqlstate '40001' using message='emlis_frame_target_changed'; end if;
    end loop;
    if p_next->'data'->'frame_target_dependencies' is distinct from
      (public.emlis_thread_related_context(p_user_id,p_input_id,
         coalesce(p_next->'data'->'context_guards','[]'::jsonb))->'frame_target_dependencies') then
      raise sqlstate '40001' using message='emlis_frame_target_changed'; end if;
  end if;
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

