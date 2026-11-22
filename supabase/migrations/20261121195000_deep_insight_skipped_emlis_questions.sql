-- Give the Premium records lane the owner's explicitly dismissed questions
-- as prior wording only. All records-lane guard readers use this function.
begin;

create or replace function public.deep_insight_material(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  with profile as (
    select coalesce((select subscription_tier from public.profiles where id=p_user_id),'free') as tier,
      exists(select 1 from public.profiles where id=p_user_id
        and coalesce(subscription_tier,'free') in ('free','plus','premium')) as available
  ), records as (
    select e.id,e.created_at,e.memo as thought,e.memo_action as action,
      encode(sha256(convert_to(public.emlis_parent_source(e)::text,'UTF8')),'hex') as source_version,
      pending.prompt as emlis_open_question,pending.question_id as emlis_open_question_id,
      coalesce(answers.items,'[]'::jsonb) as emlis_answered_questions,
      skipped.prompt as emlis_skipped_question
    from public.emotions e cross join profile
    left join public.emlis_input_threads t on t.original_emotion_id=e.id and t.user_id=e.user_id
    left join lateral (
      select q.question_id,q.payload->>'prompt_private' as prompt
      from public.emlis_thread_events q
      where t.state='AWAITING_ANSWER' and t.source_snapshot=public.emlis_parent_source(e)
        and coalesce(t.data->>'evaluated_tier',profile.tier)=profile.tier
        and q.thread_id=t.id and q.kind='QUESTION' and q.round_index=t.issued_count
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=q.thread_id
          and v.seq>q.seq and (v.kind='TERMINAL' or v.kind='ANSWER' or
            (v.kind='OPERATION' and (v.payload ? 'question_ending' or
              v.payload->>'stage'='INTERPRETATION_CORRECTION'))))
      order by q.seq desc limit 1
    ) pending on true
    left join lateral (
      select jsonb_agg(jsonb_build_object('id',a.id,'question_id',q.question_id,'answered_at',a.recorded_at,
        'source_version',encode(sha256(convert_to((a.payload->'source')::text,'UTF8')),'hex'),
        'question',q.payload->>'prompt_private','answer',a.payload#>>'{source,answer_text_private}')
        order by q.seq) as items
      from public.emlis_thread_events q join public.emlis_thread_events a
        on a.thread_id=q.thread_id and a.question_id=q.question_id and a.kind='ANSWER'
        and a.round_index=q.round_index and a.seq>q.seq
      where q.thread_id=t.id and q.kind='QUESTION' and t.source_snapshot=public.emlis_parent_source(e)
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and a.payload#>>'{source,answer_id}'=a.id::text
        and a.payload#>>'{source,thread_id}'=t.id::text
        and a.payload#>>'{source,question_id}'=q.question_id
        and a.payload#>>'{source,round_index}'=a.round_index::text
        and a.payload#>>'{source,original_source_ref}'=t.data->>'original_source_ref'
        and a.payload#>>'{source,source_role}'='SUPPLEMENTAL_ANSWER'
        and a.payload#>>'{source,source_version}'='cocolon.cmee.supplemental_answer.v1'
        and a.payload#>>'{source,answer_text_private}' ~ '[^[:space:]]'
        -- Multi-answer and corrected threads need the Emlis effective-meaning
        -- reader. Never put an unqualified historical answer back into a prompt.
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=t.id
          and ((v.kind='ANSWER' and v.id<>a.id) or
            (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')))
    ) answers on true
    left join lateral (
      select q.payload->>'prompt_private' as prompt
      from public.emlis_thread_events q
      where profile.tier='premium' and q.thread_id=t.id and q.kind='QUESTION'
        and q.round_index=t.issued_count and t.source_snapshot=public.emlis_parent_source(e)
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and exists (
          select 1 from public.emlis_thread_events v
          where v.thread_id=q.thread_id and v.round_index=q.round_index and v.seq>q.seq
            -- These older action events use the unique question in their round
            -- without copying its ID. An explicit ID, when present, must match.
            and (v.question_id is null or v.question_id=q.question_id)
            and v.idempotency_key is not null and v.payload->>'request_fingerprint' ~ '^action-request-[0-9a-f]{64}$'
            and ((v.kind='TERMINAL' and v.payload->>'reason' in ('skip','stop'))
              or (v.kind='OPERATION' and v.payload->>'stage'='NATURAL_FINAL_REQUESTED'
                and v.payload->>'status'='RUNNING' and v.payload->>'question_ending' in ('skip','stop')))
        )
        -- A stop after an answer closes the thread, not a pending question.
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=q.thread_id and v.seq>q.seq
          and ((v.kind='ANSWER' and v.question_id=q.question_id and v.round_index=q.round_index)
            or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')))
      order by q.seq desc limit 1
    ) skipped on true
    where e.user_id=p_user_id and public.emlis_parent_visible(e.created_at,profile.tier,statement_timestamp())
      and (e.memo ~ '[^[:space:]]' or e.memo_action ~ '[^[:space:]]' or answers.items is not null)
      and coalesce(t.data->>'body_state','') <> 'SAFETY'
    order by e.created_at desc,e.id limit 8
  ), prior as (
    select q.id,q.lane,q.theme,q.question_text,q.answer_text,q.answered_at,q.issued_at,q.question_key,q.text_key,
      q.grounding_receipt,
      case when q.answered_at is not null then encode(sha256(convert_to(jsonb_build_array(
        q.id,q.question_text,q.answer_text,q.answered_at)::text,'UTF8')),'hex') end as source_version
    from public.deep_insight_questions q where q.user_id=p_user_id
    order by q.issued_at desc,q.id limit 30
  ), map_guard as materialized (
    select case when profile.available and exists(select 1 from public.analysis_observed_artifacts
      where user_id=p_user_id and source_profile='cumulative.v1')
      then public.analysis_cumulative_source_snapshot(p_user_id)->>'guard' end as value
    from profile
  ), map as (
    select jsonb_build_object('id',a.id,'generated_at',a.generated_at,
      'source_version',encode(sha256(convert_to(a.source_guard,'UTF8')),'hex'),
      'summary',left(a.content_text,1800)) as item
    from public.analysis_observed_artifacts a cross join map_guard
    where a.user_id=p_user_id and a.source_profile='cumulative.v1'
      and a.source_guard=map_guard.value
    order by a.generated_at desc,a.id desc limit 1
  )
  select jsonb_build_object(
    'records',coalesce((select jsonb_agg(case when r.emlis_skipped_question is null
      then to_jsonb(r)-'emlis_skipped_question' else to_jsonb(r) end order by r.created_at desc,r.id)
      from records r),'[]'::jsonb),
    'prior',coalesce((select jsonb_agg(to_jsonb(p) order by p.issued_at desc,p.id) from prior p),'[]'::jsonb),
    'map',(select item from map));
$$;

commit;
