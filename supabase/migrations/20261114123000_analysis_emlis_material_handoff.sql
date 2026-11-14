-- Read the latest private source-grounded Emlis material for Analysis.
-- Original/answer/correction sources remain authoritative. Ordinary generated
-- reply text is deliberately absent. Old records retain their exact snapshot
-- and guard shape; stored maps and immutable monthly references are untouched.
begin;

create or replace function public.analysis_cumulative_source_snapshot(p_user_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare members jsonb; identity_members jsonb; tier text; instant timestamptz:=statement_timestamp(); first_at timestamptz;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  if not found or tier not in ('free','plus','premium') then
    raise sqlstate '42501' using message='analysis_owner_unavailable'; end if;
  select coalesce(jsonb_agg((jsonb_build_object('original',public.emlis_parent_source(e),
    'thread',case when t.id is null then null else jsonb_build_object(
      'id',t.id,'user_id',t.user_id,'original_emotion_id',t.original_emotion_id,
      'source_snapshot',t.source_snapshot,'revision',t.revision,'issued_count',t.issued_count,
      'started_question_limit',t.started_question_limit,'data',
      jsonb_strip_nulls(jsonb_build_object(
        'runtime_profile',t.data->'runtime_profile','semantic_profile',t.data->'semantic_profile',
        'execution_mode',t.data->'execution_mode','original_source_ref',t.data->'original_source_ref'))
      || case when b.material then jsonb_strip_nulls(jsonb_build_object(
        'response_profile',t.data->'response_profile',
        'natural_meaning_profile',t.data->'natural_meaning_profile',
        'natural_meaning_as_of',t.data->'natural_meaning_as_of',
        'analysis_state',t.data->'analysis_state',
        'context_guards',t.data->'context_guards','context_feedback',t.data->'context_feedback',
        'frame_target_dependencies',t.data->'frame_target_dependencies',
        'evaluated_tier',t.data->'evaluated_tier'))
        || jsonb_build_object('analysis_material',t.data->'analysis_material')
        else '{}'::jsonb end)
      || case when b.material then jsonb_build_object('source_prefix_ref',t.source_prefix_ref)
         else '{}'::jsonb end end,
    'events',coalesce((select jsonb_agg(jsonb_build_object('id',v.id,'thread_id',v.thread_id,
      'kind',v.kind,'round_index',v.round_index,'question_id',v.question_id,
      'payload',case when b.material and v.id=b.id and not exists (
          select 1 from public.emlis_thread_events c where c.thread_id=v.thread_id
            and c.kind='OPERATION' and c.payload->>'stage'='INTERPRETATION_CORRECTION'
            and c.payload#>>'{source,target_event_id}'=v.id::text)
        then jsonb_build_object('source_prefix_ref',v.payload->'source_prefix_ref',
          'artifact',jsonb_build_object('analysis_material',v.payload#>'{artifact,analysis_material}',
            'analysis_state',v.payload#>'{artifact,analysis_state}',
            'meaning_profile',v.payload#>'{artifact,meaning_profile}'))
        else v.payload end) order by v.seq)
      from public.emlis_thread_events v where v.thread_id=t.id and (v.kind in ('QUESTION','ANSWER')
        or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')
        or (b.material and v.id=b.id)
        or (v.kind='OBSERVATION' and exists (
          select 1 from public.emlis_thread_events c where c.thread_id=v.thread_id
            and c.kind='OPERATION' and c.payload->>'stage'='INTERPRETATION_CORRECTION'
            and c.payload#>>'{source,target_event_id}'=v.id::text)))),'[]'::jsonb))
    || case when b.material then jsonb_build_object('context',
      case when public.emlis_parent_visible(e.created_at,tier,instant)
        then public.emlis_thread_related_context(p_user_id,e.id,
          coalesce(t.data->'context_guards','[]'::jsonb)) else null end)
      else '{}'::jsonb end) order by e.created_at,e.id),'[]'::jsonb),
    min(e.created_at at time zone 'UTC') into members,first_at
    from public.emotions e left join public.emlis_input_threads t on t.original_emotion_id=e.id
    left join lateral (select v.id,
      jsonb_typeof(v.payload#>'{artifact,analysis_material}')='object' as material
      from public.emlis_thread_events v where v.thread_id=t.id and v.kind='OBSERVATION'
      order by v.seq desc limit 1) b on true
    where e.user_id=p_user_id and e.created_at < instant at time zone 'UTC';
  select coalesce(jsonb_agg(m #- '{thread,revision}' order by ord),'[]'::jsonb) into identity_members
    from jsonb_array_elements(members) with ordinality as x(m,ord);
  return jsonb_build_object('tier',tier,'now',instant,'members',members,
    'period_start',coalesce(first_at,instant-interval '1 second'),'period_end',instant,
    'guard','analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      jsonb_build_object('owner',p_user_id,'members',identity_members)::text,'UTF8')),'hex'));
end;
$$;

commit;
