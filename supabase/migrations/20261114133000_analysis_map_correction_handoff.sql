-- Add independent person-authored map corrections to current Analysis sources.
-- Original/answer/correction sources remain authoritative. Ordinary generated
-- reply text is deliberately absent. Old records retain their exact snapshot
-- and guard shape; stored maps and immutable monthly references are untouched.
begin;

create or replace function public.analysis_cumulative_source_snapshot(p_user_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare members jsonb; identity_members jsonb; correction_sources jsonb; identity_body jsonb; tier text; instant timestamptz:=statement_timestamp(); first_at timestamptz;
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

-- Saved IF/intent remains its immutable at-the-time version when a later map
-- explanation is added. Reauthorize the same raw cohort and the pinned
-- append-only correction prefix, without adding new corrections to its body.
create or replace function public.analysis_if_sources_current(p_user_id uuid,p_guard text,p_refs jsonb)
returns boolean language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; raw_members jsonb; members jsonb; identity_body jsonb;
  corrections jsonb; prefix jsonb:='[]'::jsonb; correction jsonb;
begin
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  select coalesce(jsonb_agg(m order by ord),'[]'::jsonb),
    coalesce(jsonb_agg(m #- '{thread,revision}' #- '{context,now}' order by ord),'[]'::jsonb)
    into raw_members,members
    from jsonb_array_elements(snap->'members') with ordinality as x(m,ord)
    where p_refs ? (m#>>'{original,id}');
  if jsonb_array_length(members)<>jsonb_array_length(p_refs) then return false; end if;
  identity_body:=jsonb_build_object('owner',p_user_id,'members',members);
  if 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(identity_body::text,'UTF8')),'hex')=p_guard then
    return true; end if;
  corrections:=public.analysis_map_correction_sources(p_user_id,raw_members);
  for correction in select value from jsonb_array_elements(corrections) loop
    prefix:=prefix || jsonb_build_array(correction);
    if 'analysis-db-cumulative-v1:' || encode(sha256(convert_to(
      (identity_body || jsonb_build_object('map_corrections',prefix))::text,'UTF8')),'hex')=p_guard then
      return true; end if;
  end loop;
  return false;
end;
$$;

create or replace function public.analysis_cumulative_evidence(p_user_id uuid,p_id uuid,p_node text,p_month date default null)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare permitted jsonb; node jsonb; result jsonb; current_corrections jsonb; correction_evidence jsonb;
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
  return jsonb_build_object('items',result,'tier',permitted->>'subscription_tier','now',statement_timestamp())
    || case when jsonb_array_length(correction_evidence)>0
      then jsonb_build_object('map_corrections',correction_evidence) else '{}'::jsonb end;
end;
$$;


commit;
