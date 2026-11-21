-- Theme generation needs only prior questions from the selected theme.
begin;

create function public.deep_insight_theme_candidate_context(p_user_id uuid,p_theme text)
returns jsonb language sql stable security invoker set search_path='' as $$
  with issued as (
    select q.question_key,q.text_key,q.question_text,
      row_number() over (order by q.issued_at desc,q.id) as position
    from public.deep_insight_questions q
    where q.user_id=p_user_id and q.lane='theme' and q.theme=p_theme
  ), material as (
    select jsonb_build_object('questions',coalesce(jsonb_agg(
      jsonb_build_object('question_key',question_key,'text_key',text_key)
      || case when position<=30 then jsonb_build_object('question_text',question_text) else '{}'::jsonb end
      order by position),'[]'::jsonb)) as body
    from issued
  )
  select jsonb_build_object('material',body,'guard','deep-insight-theme-v1:' ||
    encode(sha256(convert_to(jsonb_build_array(p_user_id,p_theme,body)::text,'UTF8')),'hex'))
  from material;
$$;
revoke all on function public.deep_insight_theme_candidate_context(uuid,text) from public,anon,authenticated;
grant execute on function public.deep_insight_theme_candidate_context(uuid,text) to service_role;

create or replace function public.deep_insight_state_at(p_user_id uuid,p_as_of timestamptz)
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
    select plan.day,plan.tier='premium' as can_use_records,latest_theme.next_available_at,
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
  select jsonb_build_object('day',day,'can_use_theme',true,'can_use_records',can_use_records,
    'records',record_question,'theme',theme_question,
    'record_available_today',can_use_records and record_question is null and not exists (
      select 1 from public.deep_insight_questions where user_id=p_user_id and lane='records' and issued_on=day),
    'theme_available_today',active_theme_id is null,'theme_next_available_at',next_available_at,
    'history',coalesce((select jsonb_agg(data order by issued_on desc,issued_at desc,id) from history),'[]'::jsonb))
  from current_questions;
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
  -- The deployed pre-transition API supplies its original unprefixed guard.
  -- A guard from the theme-only reader is checked without loading personal material.
  if p_lane='theme' and p_material_guard like 'deep-insight-theme-v1:%' then
    material_guard := public.deep_insight_theme_candidate_context(p_user_id,p_theme)->>'guard';
  else
    material_guard := encode(sha256(convert_to(public.deep_insight_material(p_user_id)::text,'UTF8')),'hex');
  end if;
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
