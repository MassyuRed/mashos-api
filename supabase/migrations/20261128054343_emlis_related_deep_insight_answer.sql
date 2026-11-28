begin;

-- Read one earlier, explicitly grounded answer relevant to the current entry.
-- A theme answer or an anchor into an AI/derived source has no original-record
-- association here. The Emlis history guards bind the same admitted past input.
create function public.emlis_related_deep_insight_answer(
  p_user_id uuid, p_input_id uuid, p_context_guards jsonb
) returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare
  parent public.emotions;
  found_answer jsonb;
begin
  if jsonb_typeof(p_context_guards) is distinct from 'array' then return null; end if;
  if jsonb_array_length(p_context_guards) not between 1 and 6 then return null; end if;
  select e.* into parent from public.emotions e join public.profiles p on p.id=e.user_id
  where e.id=p_input_id and e.user_id=p_user_id and p.subscription_tier='premium';
  if not found or parent.created_at at time zone 'UTC'>=statement_timestamp() then return null; end if;

  select jsonb_build_object('source_record',e.id,'recorded_at',e.created_at at time zone 'UTC',
    'answered_at',q.answered_at,'answer',q.answer_text,'question_context',q.question_text,
    'ref',encode(sha256(convert_to(jsonb_build_array(q.id,q.question_text,q.answer_text,
      q.answered_at,q.grounding_receipt)::text,'UTF8')),'hex')) into found_answer
  from jsonb_array_elements(p_context_guards) as g(guard)
  join public.emotions e on e.id::text=g.guard->>0 and e.user_id=p_user_id
  left join public.emlis_input_threads t on t.original_emotion_id=e.id and t.user_id=e.user_id
  join public.deep_insight_questions q on q.user_id=p_user_id and q.lane='records'
    and q.grounding_receipt->>'source_id'=e.id::text
  cross join lateral (select public.emlis_parent_source(e)::text as original,
    case q.grounding_receipt->>'field' when 'thought' then e.memo when 'action' then e.memo_action end as body,
    case when q.grounding_receipt->>'start' ~ '^[0-9]{1,8}$'
      then (q.grounding_receipt->>'start')::int end as start_at,
    case when q.grounding_receipt->>'end' ~ '^[0-9]{1,8}$'
      then (q.grounding_receipt->>'end')::int end as end_at) source
  cross join lateral (select case when source.end_at-source.start_at between 6 and 70
    and source.end_at<=char_length(source.body)
    then substr(source.body,source.start_at+1,source.end_at-source.start_at) end as literal) proof
  where e.is_secret is false and e.created_at<parent.created_at
    and g.guard=jsonb_build_array(e.id,md5(source.original),coalesce(t.revision,0))
    and q.grounding_receipt->>'policy_version'='deep-insight.v2'
    and q.grounding_receipt->>'lane'='records'
    and q.grounding_receipt->>'source_version'=encode(sha256(convert_to(source.original,'UTF8')),'hex')
    and q.grounding_receipt->>'literal_sha256'=encode(sha256(convert_to(proof.literal,'UTF8')),'hex')
    and (strpos(coalesce(parent.memo,''),proof.literal)>0 or strpos(coalesce(parent.memo_action,''),proof.literal)>0)
    and q.issued_at>=e.created_at at time zone 'UTC' and q.answered_at>=q.issued_at
    and q.answered_at<parent.created_at at time zone 'UTC' and q.answer_text~'[^[:space:]]'
    and coalesce(t.data->>'body_state','')<>'SAFETY'
    and not exists(select 1 from public.emlis_thread_events v where v.thread_id=t.id
      and v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')
    and (select count(*) from public.emlis_thread_events v where v.thread_id=t.id and v.kind='ANSWER')<2
  order by q.answered_at desc,q.id limit 1;

  return found_answer;
end;
$$;

revoke all on function public.emlis_related_deep_insight_answer(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.emlis_related_deep_insight_answer(uuid,uuid,jsonb) to service_role;

commit;
