-- Extend the existing three Piece source fences for captured frame target owners.
-- Preserve source lock order, quotas, RLS/ACL and public function signatures.
BEGIN;
DO $migration$
DECLARE
  signature text;
  target regprocedure;
  definition text;
  old_context text := $old_context$current_context := CASE
                WHEN source_thread.data->>'response_profile'='natural_reply.v1' THEN
                    public.emlis_thread_related_context(p_owner_user_id,r.source_input_id::uuid,context_guards)
                ELSE public.emlis_thread_context(p_owner_user_id,r.source_input_id::uuid) END;$old_context$;
  new_context text := $new_context$IF source_thread.data ? 'frame_target_dependencies' THEN
                FOR g IN SELECT value FROM jsonb_array_elements(source_thread.data->'frame_target_dependencies')
                    ORDER BY value->>2,value->>4 LOOP
                    PERFORM 1 FROM public.emotions b
                        JOIN public.emlis_input_threads bt ON bt.original_emotion_id=b.id AND bt.user_id=p_owner_user_id
                        JOIN public.emlis_thread_events v ON v.thread_id=bt.id AND v.id=(g->>4)::uuid
                        WHERE b.id=(g->>2)::uuid AND b.user_id=p_owner_user_id
                          AND md5(public.emlis_parent_source(b)::text)=g->>3 AND md5(v.payload::text)=g->>5
                        FOR SHARE OF b,bt,v;
                    IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONTEXT_CHANGED'; END IF;
                END LOOP;
            END IF;
            current_context := CASE
                WHEN source_thread.data->>'response_profile'='natural_reply.v1' THEN
                    public.emlis_thread_related_context(p_owner_user_id,r.source_input_id::uuid,context_guards)
                ELSE public.emlis_thread_context(p_owner_user_id,r.source_input_id::uuid) END;
            IF source_thread.data ? 'frame_target_dependencies' AND
                source_thread.data->'frame_target_dependencies' IS DISTINCT FROM
                    current_context->'frame_target_dependencies' THEN
                RAISE EXCEPTION 'PIECE_CONTEXT_CHANGED';
            END IF;$new_context$;
  old_ref text := $old_ref$                IF refined_observation.payload->>'context_ref' IS DISTINCT FROM natural_context_ref$old_ref$;
  new_ref text := $new_ref$                IF jsonb_array_length(coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb))>0 THEN
                    SELECT '['||coalesce(string_agg(to_jsonb(
                        (x.value->>0)||':'||(x.value->>1)||':'||(x.value->>2)||':'||
                        (x.value->>3)||':'||(x.value->>4)||':'||(x.value->>5))::text,
                        ',' ORDER BY x.ordinality),'')||']' INTO natural_target_tokens
                        FROM jsonb_array_elements(source_thread.data->'frame_target_dependencies') WITH ORDINALITY x(value,ordinality);
                    natural_context_ref := 'context-frame-targets-'||encode(sha256(convert_to(
                        '['||to_jsonb(natural_context_ref)::text||','||natural_target_tokens||']','UTF8')),'hex');
                END IF;
                IF refined_observation.payload->>'context_ref' IS DISTINCT FROM natural_context_ref$new_ref$;
BEGIN
  FOREACH signature IN ARRAY ARRAY[
    'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
    'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
    'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'] LOOP
    target := to_regprocedure(signature);
    IF target IS NULL THEN RAISE EXCEPTION 'PIECE_FRAME_TARGET_PRECONDITION'; END IF;
    definition := pg_get_functiondef(target);
    IF (length(definition)-length(replace(definition,old_context,'')))/length(old_context)<>1
       OR (length(definition)-length(replace(definition,old_ref,'')))/length(old_ref)<>1
       OR (length(definition)-length(replace(definition,'        natural_context_ref text;','')))/length('        natural_context_ref text;')<>1 THEN
      RAISE EXCEPTION 'PIECE_FRAME_TARGET_DEFINITION_CHANGED';
    END IF;
    EXECUTE replace(replace(replace(definition,old_context,new_context),old_ref,new_ref),
        '        natural_context_ref text;', E'        natural_context_ref text;\n        natural_target_tokens text;');
  END LOOP;
END;
$migration$;
COMMIT;
