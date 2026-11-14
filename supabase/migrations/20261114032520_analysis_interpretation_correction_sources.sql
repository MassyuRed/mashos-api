-- Preserve person-authored corrections and their exact AI target locator.
-- Only user explanations become Analysis evidence; target OBS is control.
-- Existing service-role ACL, invoker policy, monthly artifacts and no-correction
-- identity remain unchanged. No table or stored person data is rewritten.
begin;

create or replace function public.analysis_cumulative_source_snapshot(p_user_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare members jsonb; identity_members jsonb; tier text; instant timestamptz:=statement_timestamp(); first_at timestamptz;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  if not found or tier not in ('free','plus','premium') then
    raise sqlstate '42501' using message='analysis_owner_unavailable'; end if;
  select coalesce(jsonb_agg(jsonb_build_object('original',public.emlis_parent_source(e),
    'thread',case when t.id is null then null else jsonb_build_object(
      'id',t.id,'user_id',t.user_id,'original_emotion_id',t.original_emotion_id,
      'source_snapshot',t.source_snapshot,'revision',t.revision,'issued_count',t.issued_count,
      'started_question_limit',t.started_question_limit,'data',jsonb_strip_nulls(jsonb_build_object(
        'runtime_profile',t.data->'runtime_profile','semantic_profile',t.data->'semantic_profile',
        'execution_mode',t.data->'execution_mode','original_source_ref',t.data->'original_source_ref'))) end,
    'events',coalesce((select jsonb_agg(jsonb_build_object('id',v.id,'thread_id',v.thread_id,
      'kind',v.kind,'round_index',v.round_index,'question_id',v.question_id,'payload',v.payload) order by v.seq)
      from public.emlis_thread_events v where v.thread_id=t.id and (v.kind in ('QUESTION','ANSWER')
        or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')
        or (v.kind='OBSERVATION' and exists (
          select 1 from public.emlis_thread_events c where c.thread_id=v.thread_id
            and c.kind='OPERATION' and c.payload->>'stage'='INTERPRETATION_CORRECTION'
            and c.payload#>>'{source,target_event_id}'=v.id::text)))),'[]'::jsonb))
    order by e.created_at,e.id),'[]'::jsonb), min(e.created_at at time zone 'UTC')
    into members,first_at
    from public.emotions e left join public.emlis_input_threads t on t.original_emotion_id=e.id
    where e.user_id=p_user_id and e.created_at < instant at time zone 'UTC';
  select coalesce(jsonb_agg(m #- '{thread,revision}' order by ord),'[]'::jsonb) into identity_members
    from jsonb_array_elements(members) with ordinality as x(m,ord);
  return jsonb_build_object('tier',tier,'now',instant,'members',members,
    'period_start',coalesce(first_at,instant-interval '1 second'),'period_end',instant,
    'guard','analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      jsonb_build_object('owner',p_user_id,'members',identity_members)::text,'UTF8')),'hex'));
end;
$$;

create or replace function public.analysis_cumulative_evidence(p_user_id uuid,p_id uuid,p_node text,p_month date default null)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare permitted jsonb; node jsonb; result jsonb;
begin
  permitted:=public.analysis_cumulative_read(p_user_id,p_id,false,1,0,p_month);
  if jsonb_array_length(permitted->'items')=0 then
    raise sqlstate 'P0002' using message='analysis_report_unavailable'; end if;
  select n into node from public.analysis_observed_artifacts a,
    jsonb_array_elements(a.private_evidence->'graph'->'nodes') n
    where a.id=p_id and a.user_id=p_user_id and n->>'node_ref'=p_node;
  if node is null then raise sqlstate 'P0002' using message='analysis_evidence_unavailable'; end if;
  select coalesce(jsonb_agg(jsonb_build_object('original',public.emlis_parent_source(e),
    'thread',case when t.id is null then null else to_jsonb(t) end,
    'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq) from public.emlis_thread_events v
      where v.thread_id=t.id and (v.kind in ('QUESTION','ANSWER')
        or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')
        or (v.kind='OBSERVATION' and exists (
          select 1 from public.emlis_thread_events c where c.thread_id=v.thread_id
            and c.kind='OPERATION' and c.payload->>'stage'='INTERPRETATION_CORRECTION'
            and c.payload#>>'{source,target_event_id}'=v.id::text)))),'[]'::jsonb),
    'expected_envelopes',(select coalesce(jsonb_agg(distinct r->>'source_envelope_id'),'[]'::jsonb)
      from jsonb_array_elements(node->'evidence_refs') r
      where s->'child_source_envelope_refs' ? (r->>'source_envelope_id')),
    'analyzed_version',s->>'saved_record_version') order by e.created_at,e.id),'[]'::jsonb)
    into result from public.emotions e left join public.emlis_input_threads t on t.original_emotion_id=e.id
    join public.analysis_observed_artifacts a on a.id=p_id,
    jsonb_array_elements(a.private_evidence->'source_members') s
    where e.user_id=p_user_id and a.user_id=p_user_id and node->'record_refs' ? e.id::text
      and s->>'saved_record_ref'=e.id::text;
  return jsonb_build_object('items',result,'tier',permitted->>'subscription_tier','now',statement_timestamp());
end;
$$;

commit;
