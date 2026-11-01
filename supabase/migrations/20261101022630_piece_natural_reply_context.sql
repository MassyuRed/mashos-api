-- Keep Piece's consumed Emlis context aligned with the saved reply profile.
-- Only the three existing source-fenced operations change. Their row-lock order,
-- post-wait clock, source/revision checks, quotas and ACLs stay in place.
begin;
do $migration$
declare
  target regprocedure;
  definition text;
  changed integer := 0;
  old_context text := 'current_context := public.emlis_thread_context(p_owner_user_id,r.source_input_id::uuid);';
  new_context text := $replacement$current_context := CASE
                WHEN source_thread.data->>'response_profile'='natural_reply.v1' THEN
                    public.emlis_thread_related_context(p_owner_user_id,r.source_input_id::uuid,context_guards)
                ELSE public.emlis_thread_context(p_owner_user_id,r.source_input_id::uuid) END;$replacement$;
  old_lifetime text := $replacement$OR history_time < at_time AT TIME ZONE 'UTC' -
                        (CASE WHEN tier='premium' THEN interval '3650 days' ELSE interval '365 days' END) THEN$replacement$;
  new_lifetime text := $replacement$OR (source_thread.data->>'response_profile' IS DISTINCT FROM 'natural_reply.v1'
                       AND history_time < at_time AT TIME ZONE 'UTC' -
                        (CASE WHEN tier='premium' THEN interval '3650 days' ELSE interval '365 days' END)) THEN$replacement$;
begin
  if to_regprocedure('public.emlis_thread_related_context(uuid,uuid,jsonb)') is null then
    raise exception 'PIECE_NATURAL_CONTEXT_PRECONDITION';
  end if;
  for target in
    select p.oid::regprocedure from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname in
      ('piece_issue_preview_v2','piece_save_v2','piece_mutate_preview_visual_v2')
      and 'p_expected_source_state'=any(p.proargnames)
  loop
    definition := pg_get_functiondef(target);
    if (length(definition)-length(replace(definition,old_context,'')))/length(old_context) <> 1
       or (length(definition)-length(replace(definition,old_lifetime,'')))/length(old_lifetime) <> 1 then
      raise exception 'PIECE_NATURAL_CONTEXT_SOURCE_CHANGED';
    end if;
    execute replace(replace(definition,old_context,new_context),old_lifetime,new_lifetime);
    changed := changed+1;
  end loop;
  if changed <> 3 then raise exception 'PIECE_NATURAL_CONTEXT_TARGET_CHANGED'; end if;
end;
$migration$;
commit;
