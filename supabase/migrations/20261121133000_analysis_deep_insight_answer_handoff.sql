-- DeepInsight is an independent owner-authored analysis source. The issued
-- question remains framing, while the answer is the only quotable body.
begin;

create function public.analysis_deep_insight_member(p_question public.deep_insight_questions)
returns jsonb language sql stable security invoker set search_path='' as $$
  select jsonb_build_object(
    'original',jsonb_build_object('id',p_question.id,'created_at',p_question.answered_at,
      'memo',p_question.answer_text,'memo_action','','category','[]'::jsonb,
      'emotions','[]'::jsonb,'emotion_details','[]'::jsonb),
    'thread',null,'events','[]'::jsonb,
    'deep_insight',jsonb_build_object('user_id',p_question.user_id,'lane',p_question.lane,
      'theme',p_question.theme,'question_text',p_question.question_text,'issued_on',p_question.issued_on));
$$;
revoke all on function public.analysis_deep_insight_member(public.deep_insight_questions)
  from public,anon,authenticated,service_role;
-- The existing invoker snapshot and evidence RPCs are restricted to this role.
grant execute on function public.analysis_deep_insight_member(public.deep_insight_questions) to service_role;

create or replace function public.analysis_cumulative_source_snapshot(p_user_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare members jsonb; identity_members jsonb; correction_sources jsonb; identity_body jsonb; tier text; instant timestamptz:=statement_timestamp(); first_at timestamptz; answer_first timestamptz; answer_members jsonb;
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
  select coalesce(jsonb_agg(public.analysis_deep_insight_member(q) order by q.answered_at,q.id),'[]'::jsonb),
    min(q.answered_at) into answer_members,answer_first
    from public.deep_insight_questions q
    where q.user_id=p_user_id and q.answered_at<instant;
  if answer_first is not null then
    -- Keep authored answers independent; sort them together with the existing
    -- inputs without altering any old member's scope or commitment.
    select jsonb_agg(member order by
      case when member ? 'deep_insight' then (member#>>'{original,created_at}')::timestamptz
        else (member#>>'{original,created_at}')::timestamp at time zone 'UTC' end,
      member#>>'{original,id}') into members
      from jsonb_array_elements(members || answer_members) member;
    first_at:=least(first_at,answer_first);
  end if;
  select coalesce(jsonb_agg(m #- '{thread,revision}' #- '{context,now}' order by ord),'[]'::jsonb) into identity_members
    from jsonb_array_elements(members) with ordinality as x(m,ord);
  correction_sources:=public.analysis_map_correction_sources(p_user_id,members);
  identity_body:=jsonb_build_object('owner',p_user_id,'members',identity_members);
  if jsonb_array_length(correction_sources)>0 then
    identity_body:=identity_body || jsonb_build_object('map_corrections',correction_sources);
  end if;
  return jsonb_build_object('tier',tier,'now',instant,'members',members,
    'period_start',coalesce(first_at,instant-interval '1 second'),'period_end',instant,
    'guard','analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      identity_body::text,'UTF8')),'hex'))
    || case when jsonb_array_length(correction_sources)>0
      then jsonb_build_object('map_corrections',correction_sources) else '{}'::jsonb end;
end;
$$;

create or replace function public.analysis_cumulative_evidence(p_user_id uuid,p_id uuid,p_node text,p_month date default null)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare permitted jsonb; node jsonb; result jsonb; current_corrections jsonb; correction_evidence jsonb; answer_evidence jsonb;
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
  select coalesce(jsonb_agg(public.analysis_deep_insight_member(q) || jsonb_build_object(
    'expected_envelopes',(select coalesce(jsonb_agg(distinct r->>'source_envelope_id'),'[]'::jsonb)
      from jsonb_array_elements(node->'evidence_refs') r
      where s->'child_source_envelope_refs' ? (r->>'source_envelope_id')),
    'analyzed_version',s->>'saved_record_version') order by q.answered_at,q.id),'[]'::jsonb)
    into answer_evidence from public.deep_insight_questions q
    join public.analysis_observed_artifacts a on a.id=p_id,
    jsonb_array_elements(a.private_evidence->'source_members') s
    where q.user_id=p_user_id and a.user_id=p_user_id and q.answered_at is not null
      and node->'record_refs' ? q.id::text and s->>'saved_record_ref'=q.id::text;
  current_corrections:=public.analysis_map_correction_sources(p_user_id,
    public.analysis_cumulative_source_snapshot(p_user_id)->'members');
  select coalesce(jsonb_agg(jsonb_build_object('saved',saved,'current',
      (select current from jsonb_array_elements(current_corrections) current
       where current->>'correction_id'=saved#>>'{source,correction_id}'))),'[]'::jsonb)
    into correction_evidence from public.analysis_observed_artifacts a,
      jsonb_array_elements(coalesce(a.private_evidence#>'{graph,map_correction_sources}','[]'::jsonb)) saved
    where a.id=p_id and a.user_id=p_user_id and exists(
      select 1 from jsonb_array_elements(node->'evidence_refs') r
      where r->>'source_envelope_id'=saved->>'source_envelope_id');
  return jsonb_build_object('items',result || answer_evidence,'tier',permitted->>'subscription_tier','now',statement_timestamp())
    || case when jsonb_array_length(correction_evidence)>0
      then jsonb_build_object('map_corrections',correction_evidence) else '{}'::jsonb end;
end;
$$;

-- A removed answer must not remain discoverable in an old monthly map or in
-- a correction that captured the former response. Other owners' rows stay put.
create function public.analysis_deep_insight_source_deleted() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if old.answered_at is null then return null; end if;
  delete from public.analysis_map_interpretation_corrections c
    where c.user_id=old.user_id and exists (
      select 1 from jsonb_array_elements(c.target_context->'cohort') dependency
      where dependency->>'record_ref'=old.id::text);
  delete from public.analysis_observed_artifacts a where a.user_id=old.user_id
    and a.source_profile='cumulative.v1'
    and ((a.private_evidence->'source_record_refs') ? old.id::text or exists (
      select 1 from jsonb_array_elements(a.private_evidence->'source_members') s
      where s->>'saved_record_ref'=old.id::text));
  return null;
end;
$$;
revoke all on function public.analysis_deep_insight_source_deleted()
  from public,anon,authenticated,service_role;
create trigger analysis_deep_insight_source_delete
  after delete on public.deep_insight_questions
  for each row execute function public.analysis_deep_insight_source_deleted();

commit;
