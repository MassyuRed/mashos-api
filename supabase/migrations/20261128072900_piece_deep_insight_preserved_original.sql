begin;

-- A certified supplemental ADD can coexist with the selected original.
-- The supplemental text belongs to its own selector and is never returned here.
create function public.piece_deep_insight_original_still_active(p_thread public.emlis_input_threads, p_original jsonb)
returns boolean language plpgsql stable security invoker set search_path='' as $$
declare
  answer_count integer;
  material jsonb;
  checkpoint_updates jsonb;
begin
  select count(*) into answer_count from public.emlis_thread_events e
    where e.thread_id=p_thread.id and e.kind='ANSWER';
  if answer_count=0 then return true; end if;
  if (answer_count=1 and p_thread.state='COMPLETED'
      and p_thread.issued_count=1
      and p_thread.data->>'body_state'='REFINED'
      and p_thread.data->>'evaluated_tier'='premium'
      and p_thread.data->>'response_profile'='natural_reply.v1'
      and p_thread.data->>'natural_response_stage'='REFINED'
      and p_thread.data->>'answer_assessment'='RESOLVED'
      and p_thread.data->>'failure_code' is null
      and p_thread.data->>'natural_meaning_profile'='source_grounded_active_meaning.v1') is not true
    then return false; end if;

  select o.payload#>'{artifact,analysis_material}',m.payload#>'{answer_update,updates}'
    into material,checkpoint_updates
    from public.emlis_thread_events a
    join public.emlis_thread_events m on m.thread_id=a.thread_id and m.id=p_thread.current_meaning_event_id
    join public.emlis_thread_events o on o.thread_id=a.thread_id and o.id=p_thread.last_observation_event_id
    where a.thread_id=p_thread.id and a.id=p_thread.latest_answer_event_id
      and a.kind='ANSWER' and a.round_index=1 and a.seq<m.seq and m.seq<o.seq
      and m.kind='MEANING_UPDATE' and m.round_index=1
      and m.payload->>'semantic_schema_version'='cocolon.cmee.emlis_answer_meaning.v1'
      and m.payload->>'source_prefix_ref'=p_thread.source_prefix_ref
      and m.payload->>'assessment_status'='RESOLVED' and m.payload->'unresolved_parts'='[]'::jsonb
      and m.payload#>>'{answer_update,disposition}'='MATERIAL_UPDATE'
      and m.payload#>'{answer_update,unresolved_parts}'='[]'::jsonb
      and o.kind='OBSERVATION' and o.round_index=1 and o.payload->>'stage'='REFINED'
      and o.payload->>'source_prefix_ref'=p_thread.source_prefix_ref
      and not (o.payload ? 'meaning_checkpoint_ref')
      and o.operation_id=a.operation_id and o.attempt_id=a.attempt_id
      and o.operation_id=m.operation_id and o.attempt_id=m.attempt_id
      and o.operation_id::text=p_thread.data->>'operation_id'
      and o.attempt_id::text=p_thread.data->>'attempt_id'
      and exists(select 1 from public.emlis_thread_events e where e.thread_id=o.thread_id
        and e.kind='OPERATION' and e.operation_id=o.operation_id and e.attempt_id=o.attempt_id
        and e.seq>o.seq and e.payload->>'status'='COMPLETED' and e.payload->>'failure_code' is null)
      and public.piece_natural_analysis_artifact_valid(
        o.payload->'artifact',p_thread.source_prefix_ref,p_thread.user_id,p_original)
      and o.payload#>'{artifact,analysis_material}'=p_thread.data->'analysis_material'
      and o.payload#>>'{artifact,analysis_material,coverage,active_state}'='RESOLVED'
      and o.payload#>'{artifact,analysis_material,graph,source_updates}'='[]'::jsonb;

  if not found or jsonb_typeof(checkpoint_updates) is distinct from 'array' then return false; end if;
  if jsonb_array_length(checkpoint_updates)=0 or exists (
    select 1 from jsonb_array_elements(checkpoint_updates) item
    where (item->>'operation'='ADD' and item->'superseded_claim_refs'='[]'::jsonb
      and item->'affected_dependency_refs'='[]'::jsonb) is not true
  ) then return false; end if;

  return not exists (
    select 1 from jsonb_each_text(p_original) original(field_name,body)
    where original.field_name in ('memo','memo_action') and original.body ~ '[^[:space:]]'
      and not exists (
        select 1 from jsonb_array_elements(material->'active_fields') f
        where f->>'source_role'='ORIGINAL_INPUT' and f->>'source_id'=p_original->>'id'
          and f->>'record_ref'=p_original->>'id' and f->>'record_version'=material->>'record_version'
          and f->>'field_path'=original.field_name and f->>'scalar_start'='0'
          and f->>'scalar_end'=char_length(original.body)::text and f->>'text'=original.body
          and f#>>'{evidence,literal_sha256}'=encode(sha256(convert_to(original.body,'UTF8')),'hex')
      )
  );
end;
$$;
revoke all on function public.piece_deep_insight_original_still_active(public.emlis_input_threads,jsonb)
  from public,anon,authenticated;
grant execute on function public.piece_deep_insight_original_still_active(public.emlis_input_threads,jsonb)
  to service_role;

do $migration$
declare
  definition text;
  source_guard text := $old$exists(select 1 from public.emlis_thread_events e
      where e.thread_id=thread.id and e.kind='ANSWER')$old$;
  history_guard text := $old$(ev.kind='ANSWER' or (ev.kind='OPERATION' and ev.payload->>'stage'='INTERPRETATION_CORRECTION'))$old$;
  history_anchor text := $old$and not exists(select 1 from public.emlis_thread_events ev where ev.thread_id=t.id$old$;
begin
  definition:=pg_get_functiondef('public.piece_deep_insight_source_binding(uuid,uuid,uuid,text)'::regprocedure);
  if (length(definition)-length(replace(definition,source_guard,'')))<>length(source_guard)
    then raise exception 'PIECE_DEEP_INSIGHT_SOURCE_GUARD_CHANGED'; end if;
  execute replace(definition,source_guard,
    'not public.piece_deep_insight_original_still_active(thread,original)');

  definition:=pg_get_functiondef('public.deep_insight_piece_history_links(uuid,uuid[])'::regprocedure);
  if (length(definition)-length(replace(definition,history_guard,'')))<>length(history_guard)
    or (length(definition)-length(replace(definition,history_anchor,'')))<>length(history_anchor)
    then raise exception 'PIECE_DEEP_INSIGHT_HISTORY_GUARD_CHANGED'; end if;
  definition:=replace(definition,history_guard,
    $new$(ev.kind='OPERATION' and ev.payload->>'stage'='INTERPRETATION_CORRECTION')$new$);
  execute replace(definition,history_anchor,
    'and public.piece_deep_insight_original_still_active(t,public.emlis_parent_source(e)) '||history_anchor);
end;
$migration$;

commit;
