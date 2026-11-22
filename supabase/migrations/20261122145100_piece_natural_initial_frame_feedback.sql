-- Bind the first owned past-frame decision to all three Piece write paths.
BEGIN;
DO $migration$
DECLARE
    signature text;
    definition text;
    old_event text := $old$initial_frame_event.payload->>'status'='FRAME_REVISED'$old$;
    new_event text := $new$initial_frame_event.payload->>'status' IN ('FRAME_CONFIRMED','FRAME_REJECTED','FRAME_REVISED')$new$;
    old_status text := $old$f->>'status'='REVISED' AND f->'version'='1'::jsonb$old$;
    new_status text := $new$'FRAME_'||(f->>'status')=initial_frame_event.payload->>'status' AND f->'version'='1'::jsonb$new$;
    old_hash text := $old$'['||(f->'frame_ref')::text||',"REVISED",'||(f->'correction_text')::text||']'$old$;
    new_hash text := $new$'['||(f->'frame_ref')::text||','||(f->'status')::text||','||(f->'correction_text')::text||']'$new$;
BEGIN
    FOREACH signature IN ARRAY ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
    ] LOOP
        definition := pg_get_functiondef(signature::regprocedure);
        IF (length(definition)-length(replace(definition,old_event,'')))<>length(old_event)
           OR (length(definition)-length(replace(definition,old_status,'')))<>length(old_status)
           OR (length(definition)-length(replace(definition,old_hash,'')))<>length(old_hash) THEN
            RAISE EXCEPTION 'PIECE_NATURAL_INITIAL_FRAME_DEFINITION_CHANGED';
        END IF;
        EXECUTE replace(replace(replace(definition,old_event,new_event),old_status,new_status),old_hash,new_hash);
    END LOOP;
END;
$migration$;
COMMIT;
