-- Q2 development schema. No existing rows/tables are rewritten.
-- Private source-bearing tables; access only through the verified application API.
begin;
create table public.emlis_input_threads (
  id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  original_emotion_id uuid not null unique references public.emotions(id) on delete cascade,
  revision bigint not null check (revision > 0),
  state text not null check (state in ('INITIALIZING','AWAITING_ANSWER','REFINING','COMPLETED','RESPONSE_FAILED')),
  issued_count integer not null check (issued_count between 0 and 1),
  current_meaning_event_id uuid,
  last_observation_event_id uuid,
  latest_answer_event_id uuid,
  source_prefix_ref text,
  evaluated_prefix_ref text,
  active_operation_id uuid,
  active_attempt_id uuid,
  processing_deadline_at timestamptz,
  source_snapshot jsonb not null,
  data jsonb not null,
  created_at timestamptz not null default clock_timestamp(),
  updated_at timestamptz not null default clock_timestamp(),
  check ((active_attempt_id is null) = (active_operation_id is null)),
  check ((active_attempt_id is null) = (processing_deadline_at is null)),
  check ((state in ('INITIALIZING','REFINING')) = (active_attempt_id is not null))
);
create index emlis_threads_owner_input on public.emlis_input_threads(user_id, original_emotion_id);
create table public.emlis_thread_events (
  id uuid primary key,
  thread_id uuid not null references public.emlis_input_threads(id) on delete cascade,
  seq bigint not null check (seq > 0),
  kind text not null check (kind in ('OBSERVATION','QUESTION','ANSWER','MEANING_UPDATE','OPERATION','TERMINAL')),
  round_index integer not null check (round_index between 0 and 1),
  question_id text,
  operation_id uuid,
  attempt_id uuid,
  idempotency_key text check (char_length(idempotency_key) between 1 and 128),
  payload jsonb not null,
  recorded_at timestamptz not null default clock_timestamp(),
  unique(thread_id,seq), unique(thread_id,id),
  check (kind not in ('QUESTION','ANSWER') or question_id is not null)
);
create unique index emlis_event_operation_key on public.emlis_thread_events(thread_id,idempotency_key) where idempotency_key is not null;
create unique index emlis_answer_once on public.emlis_thread_events(thread_id,question_id) where kind='ANSWER';
create unique index emlis_question_once on public.emlis_thread_events(thread_id,round_index) where kind='QUESTION';
create unique index emlis_meaning_once on public.emlis_thread_events
  (thread_id,(payload->>'source_prefix_ref'),(payload->>'semantic_schema_version')) where kind='MEANING_UPDATE';
alter table public.emlis_input_threads add foreign key(id,current_meaning_event_id)
  references public.emlis_thread_events(thread_id,id) deferrable initially deferred;
alter table public.emlis_input_threads add foreign key(id,last_observation_event_id)
  references public.emlis_thread_events(thread_id,id) deferrable initially deferred;
alter table public.emlis_input_threads add foreign key(id,latest_answer_event_id)
  references public.emlis_thread_events(thread_id,id) deferrable initially deferred;
alter table public.emlis_input_threads enable row level security;
alter table public.emlis_thread_events enable row level security;
revoke all on public.emlis_input_threads,public.emlis_thread_events from public,anon,authenticated;
grant select,insert,update,delete on public.emlis_input_threads,public.emlis_thread_events to service_role;

create function public.emlis_parent_source(p public.emotions) returns jsonb
language sql immutable security invoker set search_path='' as $$
  select jsonb_build_object('id',p.id,'created_at',p.created_at,'memo',p.memo,
    'memo_action',p.memo_action,'category',p.category,'emotions',p.emotions,'emotion_details',p.emotion_details);
$$;
-- Mirrors publish_governance: parent timestamps are UTC; Free uses JST months.
create function public.emlis_parent_visible(p_created timestamp,p_tier text,p_now timestamptz) returns boolean
language sql stable security invoker set search_path='' as $$
  select p_created is not null and case p_tier
    when 'premium' then true
    when 'plus' then p_created at time zone 'UTC' >= p_now - interval '365 days'
      and p_created at time zone 'UTC' < p_now + interval '1 millisecond'
    else p_created at time zone 'UTC' >= (date_trunc('month',p_now at time zone 'Asia/Tokyo') - interval '1 month') at time zone 'Asia/Tokyo'
      and p_created at time zone 'UTC' < (date_trunc('month',p_now at time zone 'Asia/Tokyo') + interval '1 month') at time zone 'Asia/Tokyo' end;
$$;
-- VOLATILE ensures the commit RPC reads its own newly appended events.
create function public.emlis_thread_read(p_user_id uuid,p_input_id uuid default null,p_thread_id uuid default null)
returns jsonb language sql volatile security invoker set search_path='' as $$
  select jsonb_build_object('original',public.emlis_parent_source(e),
    'tier',coalesce(p.subscription_tier,'free'),'now',statement_timestamp(),
    'thread',case when t.id is null then null else to_jsonb(t) end,
    'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq)
      from public.emlis_thread_events v where v.thread_id=t.id),'[]'::jsonb))
  from public.emotions e left join public.profiles p on p.id=e.user_id
  left join public.emlis_input_threads t on t.original_emotion_id=e.id
  where e.user_id=p_user_id and (t.id is null or t.user_id=p_user_id)
    and ((p_input_id is not null and e.id=p_input_id and p_thread_id is null)
    or (p_thread_id is not null and t.id=p_thread_id and p_input_id is null))
    and public.emlis_parent_visible(e.created_at,coalesce(p.subscription_tier,'free'),statement_timestamp());
$$;

-- Application owns semantics; DB owns liveness/access, revision, lease, uniqueness.
create function public.emlis_thread_commit(
  p_user_id uuid,p_input_id uuid,p_thread_id uuid,p_expected_revision bigint,
  p_source_snapshot jsonb,p_access_tier text,p_next jsonb,p_events jsonb,
  p_finishing_attempt uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare
  parent public.emotions; prior public.emlis_input_threads;
  tier text; v jsonb; n bigint; questions integer; instant timestamptz;
begin
  select * into parent from public.emotions where id=p_input_id and user_id=p_user_id for share;
  if not found then raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  select subscription_tier into tier from public.profiles where id=p_user_id for share;
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
  if prior.id is null then
    insert into public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
      values(p_thread_id,p_user_id,p_input_id,1,'COMPLETED',0,p_source_snapshot,'{}');
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
    data=p_next->'data',updated_at=instant where id=p_thread_id;
  return public.emlis_thread_read(p_user_id,p_input_id,null);
end;
$$;
revoke all on function public.emlis_parent_source(public.emotions),
  public.emlis_parent_visible(timestamp,text,timestamptz),public.emlis_thread_read(uuid,uuid,uuid),
  public.emlis_thread_commit(uuid,uuid,uuid,bigint,jsonb,text,jsonb,jsonb,uuid) from public,anon,authenticated;
grant execute on function public.emlis_parent_source(public.emotions),
  public.emlis_parent_visible(timestamp,text,timestamptz),public.emlis_thread_read(uuid,uuid,uuid),
  public.emlis_thread_commit(uuid,uuid,uuid,bigint,jsonb,text,jsonb,jsonb,uuid) to service_role;
commit;
