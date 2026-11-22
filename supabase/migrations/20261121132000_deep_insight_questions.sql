-- Owner-only issued questions. Legacy Today Question and unbound answer rows
-- keep their original provenance and are not read as DeepInsight material.
begin;

create table public.deep_insight_questions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  lane text not null check (lane in ('records','theme')),
  theme text check (char_length(theme) between 1 and 40),
  question_text text not null check (char_length(question_text) between 1 and 280),
  issued_on date not null,
  issued_at timestamptz not null default clock_timestamp(),
  question_key text not null,
  text_key text not null,
  answer_text text check (char_length(answer_text) between 1 and 2000 and answer_text ~ '[^[:space:]]'),
  answered_at timestamptz,
  check ((lane='theme') = (theme is not null)),
  check ((answer_text is null) = (answered_at is null)),
  unique (user_id,lane,issued_on),
  unique (user_id,question_key),
  unique (user_id,text_key)
);
create unique index deep_insight_one_pending_record on public.deep_insight_questions(user_id)
  where lane='records' and answer_text is null;
create index deep_insight_owner_history on public.deep_insight_questions(user_id,issued_on desc,issued_at desc,id);
alter table public.deep_insight_questions enable row level security;
revoke all on public.deep_insight_questions from public,anon,authenticated,service_role;
grant select,insert on public.deep_insight_questions to service_role;

create function public.deep_insight_question_payload(q public.deep_insight_questions)
returns jsonb language sql immutable security invoker set search_path='' as $$
  select jsonb_build_object('id',q.id,'lane',q.lane,'theme',q.theme,'question_text',q.question_text,
    'issued_on',q.issued_on,'answer_text',q.answer_text,'answered_at',q.answered_at)
  where q.id is not null;
$$;

create function public.deep_insight_state(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  with state as (
    select (statement_timestamp() at time zone 'Asia/Tokyo')::date as day,
      coalesce((select subscription_tier in ('plus','premium') from public.profiles where id=p_user_id),false) as paid
  ), current_questions as (
    select day,paid,
      (select public.deep_insight_question_payload(q) from public.deep_insight_questions q
       where user_id=p_user_id and lane='records' and answer_text is null) as record_question,
      (select public.deep_insight_question_payload(q) from public.deep_insight_questions q
       where user_id=p_user_id and lane='theme' and issued_on=day) as theme_question
    from state
  ), history as (
    select public.deep_insight_question_payload(q) as data,q.issued_on,q.issued_at,q.id
    from public.deep_insight_questions q cross join state
    where q.user_id=p_user_id and (q.answer_text is not null or (q.lane='theme' and q.issued_on<day))
    order by q.issued_on desc,q.issued_at desc,q.id limit 40
  )
  select jsonb_build_object('day',day,'can_use_theme',paid,'records',record_question,'theme',theme_question,
    'record_available_today',record_question is null and not exists (
      select 1 from public.deep_insight_questions where user_id=p_user_id and lane='records' and issued_on=day),
    'theme_available_today',paid and theme_question is null,
    'history',coalesce((select jsonb_agg(data order by issued_on desc,issued_at desc,id) from history),'[]'::jsonb))
  from current_questions;
$$;

create function public.deep_insight_material(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  with profile as (
    select coalesce((select subscription_tier from public.profiles where id=p_user_id),'free') as tier
  ), records as (
    select e.id,e.created_at,e.memo as thought,e.memo_action as action,
      (select q.payload->>'prompt_private' from public.emlis_thread_events q
       where q.thread_id=t.id and q.kind='QUESTION'
         and not exists (select 1 from public.emlis_thread_events a where a.thread_id=t.id
           and a.kind='ANSWER' and a.question_id=q.question_id)
       order by q.seq desc limit 1) as emlis_open_question,
      coalesce((select jsonb_agg(jsonb_build_object('question',q.payload->>'prompt_private',
        'answer',a.payload#>>'{source,answer_text_private}') order by q.seq)
        from public.emlis_thread_events q join public.emlis_thread_events a
          on a.thread_id=q.thread_id and a.question_id=q.question_id and a.kind='ANSWER'
        where q.thread_id=t.id and q.kind='QUESTION'), '[]'::jsonb) as emlis_answered_questions
    from public.emotions e cross join profile
    left join public.emlis_input_threads t on t.original_emotion_id=e.id and t.user_id=e.user_id
    where e.user_id=p_user_id and public.emlis_parent_visible(e.created_at,profile.tier,statement_timestamp())
      and (e.memo ~ '[^[:space:]]' or e.memo_action ~ '[^[:space:]]')
      and coalesce(t.data->>'body_state','') <> 'SAFETY'
    order by e.created_at desc,e.id limit 8
  ), prior as (
    select q.id,q.lane,q.theme,q.question_text,q.answer_text,q.answered_at,q.issued_at,q.question_key,q.text_key
    from public.deep_insight_questions q where q.user_id=p_user_id
    order by q.issued_at desc,q.id limit 30
  )
  select jsonb_build_object(
    'records',coalesce((select jsonb_agg(to_jsonb(r) order by r.created_at desc,r.id) from records r),'[]'::jsonb),
    'prior',coalesce((select jsonb_agg(to_jsonb(p) order by p.issued_at desc,p.id) from prior p),'[]'::jsonb),
    'map', (select jsonb_build_object('generated_at',a.generated_at,'summary',left(a.content_text,1800))
      from public.analysis_observed_artifacts a where a.user_id=p_user_id and a.source_profile='cumulative.v1'
      order by a.generated_at desc,a.id desc limit 1));
$$;

create function public.deep_insight_issue(p_user_id uuid,p_day date,p_lane text,p_theme text,
  p_question_text text,p_question_key text,p_text_key text,p_material_guard text)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  state jsonb;
  current_question jsonb;
  saved public.deep_insight_questions;
  material_guard text;
begin
  if p_lane is null or p_lane not in ('records','theme') or p_day is null then
    raise sqlstate '22023' using message='deep_insight_request_invalid';
  end if;
  -- The same owner can open two devices or request both entrances together.
  perform pg_advisory_xact_lock(hashtextextended('deep-insight:' || p_user_id::text,0));
  state := public.deep_insight_state(p_user_id);
  if p_lane='theme' and not (state->>'can_use_theme')::boolean then
    raise sqlstate '42501' using message='deep_insight_theme_locked';
  end if;
  current_question := state->p_lane;
  if current_question <> 'null'::jsonb then
    return jsonb_build_object('status','existing','question',current_question);
  end if;
  if not (state->>(case when p_lane='records' then 'record_available_today' else 'theme_available_today' end))::boolean then
    return jsonb_build_object('status','daily_limit','question',null);
  end if;
  if p_day is distinct from (state->>'day')::date then
    return jsonb_build_object('status','no_question','question',null);
  end if;
  material_guard := encode(sha256(convert_to(public.deep_insight_material(p_user_id)::text,'UTF8')),'hex');
  if p_material_guard is distinct from material_guard then
    return jsonb_build_object('status','no_question','question',null);
  end if;
  insert into public.deep_insight_questions(user_id,lane,theme,question_text,issued_on,question_key,text_key)
  values(p_user_id,p_lane,p_theme,p_question_text,p_day,p_question_key,p_text_key)
  on conflict do nothing returning * into saved;
  if not found then
    return jsonb_build_object('status','no_question','question',null);
  end if;
  return jsonb_build_object('status','issued','question',public.deep_insight_question_payload(saved));
end;
$$;

create function public.deep_insight_candidate_context(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  select jsonb_build_object('material',m,'guard',encode(sha256(convert_to(m::text,'UTF8')),'hex'))
  from (select public.deep_insight_material(p_user_id) as m) s;
$$;

-- The owner row lock also protects the existing cumulative MAP commit. The
-- caller is the verified-owner application, never an authenticated DB client.
create function public.deep_insight_answer(p_user_id uuid,p_question_id uuid,p_answer_text text)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
declare q public.deep_insight_questions;
begin
  if p_answer_text is null or char_length(p_answer_text)>2000 or p_answer_text !~ '[^[:space:]]' then
    raise sqlstate '22023' using message='deep_insight_answer_required';
  end if;
  perform 1 from auth.users where id=p_user_id for update;
  if not found then raise sqlstate 'P0002' using message='deep_insight_question_unavailable'; end if;
  select * into q from public.deep_insight_questions where user_id=p_user_id and id=p_question_id for update;
  if not found then raise sqlstate 'P0002' using message='deep_insight_question_unavailable'; end if;
  if q.answer_text is not null then
    if q.answer_text <> p_answer_text then
      raise sqlstate '23505' using message='deep_insight_answer_conflict';
    end if;
    return jsonb_build_object('question',public.deep_insight_question_payload(q),'inserted',false);
  end if;
  update public.deep_insight_questions set answer_text=p_answer_text,answered_at=clock_timestamp()
  where id=q.id returning * into q;
  return jsonb_build_object('question',public.deep_insight_question_payload(q),'inserted',true);
end;
$$;

revoke all on function public.deep_insight_question_payload(public.deep_insight_questions),
  public.deep_insight_state(uuid),public.deep_insight_material(uuid),public.deep_insight_candidate_context(uuid),
  public.deep_insight_issue(uuid,date,text,text,text,text,text,text),public.deep_insight_answer(uuid,uuid,text)
  from public,anon,authenticated;
grant execute on function public.deep_insight_question_payload(public.deep_insight_questions),
  public.deep_insight_state(uuid),public.deep_insight_material(uuid),public.deep_insight_candidate_context(uuid),
  public.deep_insight_issue(uuid,date,text,text,text,text,text,text),public.deep_insight_answer(uuid,uuid,text)
  to service_role;

commit;
