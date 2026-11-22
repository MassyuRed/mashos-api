-- The latest successful theme issuance starts one shared rolling allowance.
begin;

create index deep_insight_latest_theme on public.deep_insight_questions(user_id,issued_at desc,id)
  where lane='theme';

create function public.deep_insight_theme_cooldown(p_subscription_tier text)
returns interval language sql immutable security invoker set search_path='' as $$
  select case when p_subscription_tier in ('plus','premium') then interval '24 hours' else interval '168 hours' end;
$$;
revoke all on function public.deep_insight_theme_cooldown(text) from public,anon,authenticated;
grant execute on function public.deep_insight_theme_cooldown(text) to service_role;

create function public.deep_insight_state_at(p_user_id uuid,p_as_of timestamptz)
returns jsonb language sql stable security invoker set search_path='' as $$
  with plan as (
    select (p_as_of at time zone 'Asia/Tokyo')::date as day,
      coalesce((select subscription_tier from public.profiles where id=p_user_id),'free') as tier
  ), latest_theme as (
    select q.id,public.deep_insight_question_payload(q) as question,
      q.issued_at + public.deep_insight_theme_cooldown(plan.tier) as next_available_at
    from public.deep_insight_questions q cross join plan
    where q.user_id=p_user_id and q.lane='theme'
    order by q.issued_at desc,q.id limit 1
  ), current_questions as (
    select plan.day,plan.tier in ('plus','premium') as paid,latest_theme.next_available_at,
      case when latest_theme.next_available_at>p_as_of then latest_theme.id end as active_theme_id,
      case when latest_theme.next_available_at>p_as_of then latest_theme.question end as theme_question,
      (select public.deep_insight_question_payload(q) from public.deep_insight_questions q
       where q.user_id=p_user_id and q.lane='records' and q.answer_text is null) as record_question
    from plan left join latest_theme on true
  ), history as (
    select public.deep_insight_question_payload(q) as data,q.issued_on,q.issued_at,q.id
    from public.deep_insight_questions q cross join current_questions
    where q.user_id=p_user_id and (q.answer_text is not null
      or (q.lane='theme' and q.id is distinct from current_questions.active_theme_id))
    order by q.issued_on desc,q.issued_at desc,q.id limit 40
  )
  select jsonb_build_object('day',day,'can_use_theme',true,'can_use_records',paid,
    'records',record_question,'theme',theme_question,
    'record_available_today',paid and record_question is null and not exists (
      select 1 from public.deep_insight_questions where user_id=p_user_id and lane='records' and issued_on=day),
    'theme_available_today',active_theme_id is null,'theme_next_available_at',next_available_at,
    'history',coalesce((select jsonb_agg(data order by issued_on desc,issued_at desc,id) from history),'[]'::jsonb))
  from current_questions;
$$;
revoke all on function public.deep_insight_state_at(uuid,timestamptz) from public,anon,authenticated;
grant execute on function public.deep_insight_state_at(uuid,timestamptz) to service_role;

create or replace function public.deep_insight_state(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  select public.deep_insight_state_at(p_user_id,statement_timestamp());
$$;

create or replace function public.deep_insight_issue(p_user_id uuid,p_day date,p_lane text,p_theme text,
  p_question_text text,p_question_key text,p_text_key text,p_material_guard text)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  state jsonb;
  current_question jsonb;
  saved public.deep_insight_questions;
  material_guard text;
  issue_time timestamptz;
begin
  if p_lane is null or p_lane not in ('records','theme') or p_day is null then
    raise sqlstate '22023' using message='deep_insight_request_invalid';
  end if;
  -- Recheck eligibility against the latest owner rows after any competing issue.
  perform pg_advisory_xact_lock(hashtextextended('deep-insight:' || p_user_id::text,0));
  state := public.deep_insight_state_at(p_user_id,clock_timestamp());
  current_question := state->p_lane;
  if current_question <> 'null'::jsonb then
    return jsonb_build_object('status','existing','question',current_question)
      || case when p_lane='theme'
        then jsonb_build_object('theme_next_available_at',state->'theme_next_available_at') else '{}'::jsonb end;
  end if;
  if p_lane='records' and not (state->>'can_use_records')::boolean then
    raise sqlstate '42501' using message='deep_insight_records_locked';
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
  issue_time := clock_timestamp();
  if p_day is distinct from (issue_time at time zone 'Asia/Tokyo')::date then
    return jsonb_build_object('status','no_question','question',null);
  end if;
  insert into public.deep_insight_questions(user_id,lane,theme,question_text,issued_on,issued_at,question_key,text_key)
  values(p_user_id,p_lane,p_theme,p_question_text,p_day,issue_time,p_question_key,p_text_key)
  on conflict do nothing returning * into saved;
  if not found then
    return jsonb_build_object('status','no_question','question',null);
  end if;
  if p_lane='theme' then
    state := public.deep_insight_state_at(p_user_id,saved.issued_at);
    return jsonb_build_object('status','issued','question',public.deep_insight_question_payload(saved),
      'theme_next_available_at',state->'theme_next_available_at');
  end if;
  return jsonb_build_object('status','issued','question',public.deep_insight_question_payload(saved));
end;
$$;

commit;
