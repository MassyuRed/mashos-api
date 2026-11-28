begin;

-- Link only an owner's answered record question to its still-current record.
-- This is a history selector. Preview/edit/save recheck the locked source proof.
create function public.deep_insight_piece_history_links(p_owner uuid,p_question_ids uuid[])
returns jsonb language sql stable security invoker set search_path='' as $$
  select coalesce(jsonb_object_agg(q.id::text,public.emlis_parent_source(e)),'{}'::jsonb)
  from public.deep_insight_questions q
  join public.profiles p on p.id=q.user_id and p.subscription_tier='premium'
  join public.emotions e on e.user_id=q.user_id and e.id::text=q.grounding_receipt->>'source_id'
  left join public.emlis_input_threads t on t.original_emotion_id=e.id
  where q.user_id=p_owner and cardinality(p_question_ids)<=40 and q.id=any(p_question_ids)
    and q.lane='records' and q.answer_text is not null and q.answered_at<statement_timestamp()
    and e.is_secret is false and q.issued_at>=e.created_at at time zone 'UTC'
    and public.emlis_parent_visible(e.created_at,p.subscription_tier,statement_timestamp())
    and q.grounding_receipt->>'policy_version'='deep-insight.v2'
    and q.grounding_receipt->>'lane'='records'
    and q.grounding_receipt->>'source_version'=
      encode(sha256(convert_to(public.emlis_parent_source(e)::text,'UTF8')),'hex')
    and (t.id is null or (t.user_id=q.user_id and t.source_snapshot=public.emlis_parent_source(e)
      and coalesce(t.data->>'body_state','')<>'SAFETY'
      and coalesce(t.data->>'failure_code','') not in ('safe_state_answer_owner_required','separate_safety_owner_required')
      and not exists(select 1 from public.emlis_thread_events ev where ev.thread_id=t.id and
        (ev.kind='ANSWER' or (ev.kind='OPERATION' and ev.payload->>'stage'='INTERPRETATION_CORRECTION')))));
$$;

revoke all on function public.deep_insight_piece_history_links(uuid,uuid[]) from public,anon,authenticated;
grant execute on function public.deep_insight_piece_history_links(uuid,uuid[]) to service_role;

commit;
