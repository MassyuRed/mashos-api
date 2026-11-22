-- Allow a saved one-answer reply to finish on a later attempt of the same
-- operation. The original answer, checkpoint and provider receipt stay intact.
BEGIN;
DO $migration$
DECLARE
    signature text;
    definition text;
    arm text;
    arm_start integer;
    arm_end integer;
    start_marker text := $start$            ELSIF r.source_lineage#>>'{observation,emlis_observation_stage}'='refined_observation' THEN
                IF source_thread.data->>'response_profile'='natural_reply.v1' THEN$start$;
    end_marker text := $end$                ELSIF source_thread.data->>'response_profile' IS NULL THEN$end$;
    old_attempts text := $old$                    AND refined_answer.attempt_id=refined_observation.attempt_id
                    AND refined_checkpoint.operation_id=refined_observation.operation_id
                    AND refined_checkpoint.attempt_id=refined_observation.attempt_id$old$;
    new_attempts text := $new$                    AND refined_checkpoint.operation_id=refined_observation.operation_id
                    AND refined_answer.attempt_id=refined_checkpoint.attempt_id
                    AND (refined_answer.attempt_id=refined_observation.attempt_id OR source_thread.issued_count=1)$new$;
    old_author text := $old$                        AND natural_started.attempt_id=natural_body.attempt_id
                        AND natural_received.attempt_id=natural_body.attempt_id$old$;
    new_author text := $new$                        AND natural_started.attempt_id=natural_received.attempt_id
                        AND CASE WHEN natural_body.id=refined_observation.id AND source_thread.issued_count=1 THEN
                            natural_received.attempt_id=refined_checkpoint.attempt_id
                            AND (natural_received.attempt_id=natural_body.attempt_id OR (
                                jsonb_build_array(natural_started.payload->'meaning_profile',natural_started.payload->'writer_messages_sha256')
                                    =jsonb_build_array(natural_body.payload#>'{artifact,meaning_profile}',natural_body.payload#>'{artifact,writer_messages_sha256}')
                                AND jsonb_build_array(natural_received.payload->'meaning_profile',natural_received.payload->'writer_messages_sha256')
                                    =jsonb_build_array(natural_body.payload#>'{artifact,meaning_profile}',natural_body.payload#>'{artifact,writer_messages_sha256}')
                                AND (SELECT count(*)>0 AND count(*)%2=0
                                    AND count(DISTINCT event.attempt_id) FILTER (WHERE event.i%2=0)=count(*)/2
                                    AND count(*) FILTER (WHERE event.i=event.n AND event.attempt_id=natural_body.attempt_id)=1
                                    AND bool_and((event.kind='OPERATION'
                                        AND event.operation_id=natural_body.operation_id
                                        AND event.round_index=natural_body.round_index
                                        AND event.previous_time<=event.recorded_at
                                        AND event.recorded_at<=natural_body.recorded_at
                                        AND CASE WHEN event.i%2=1 THEN
                                            event.attempt_id=event.previous_attempt
                                            AND event.payload->>'status'='RESPONSE_FAILED'
                                            AND event.payload->>'failure_code' IN ('storage_temporarily_unavailable','worker_interrupted')
                                        ELSE
                                            event.attempt_id<>natural_received.attempt_id
                                            AND event.payload->>'status'='RUNNING'
                                            AND event.question_id IS NULL
                                            AND event.payload-ARRAY['status','request_fingerprint']='{}'::jsonb
                                            AND event.idempotency_key IS NOT NULL
                                            AND event.payload->>'request_fingerprint' ~ '^action-request-[0-9a-f]{64}$'
                                        END) IS TRUE)
                                    FROM (
                                        SELECT e.kind,e.operation_id,e.round_index,e.attempt_id,e.recorded_at,e.question_id,e.idempotency_key,e.payload,
                                            row_number() OVER attempts AS i, count(*) OVER () AS n,
                                            lag(e.attempt_id,1,natural_received.attempt_id) OVER attempts AS previous_attempt,
                                            lag(e.recorded_at,1,natural_received.recorded_at) OVER attempts AS previous_time
                                        FROM public.emlis_thread_events e
                                        WHERE e.thread_id=source_thread.id AND e.seq>natural_received.seq AND e.seq<natural_body.seq
                                        WINDOW attempts AS (ORDER BY e.seq)
                                    ) event)
                            ))
                        ELSE natural_received.attempt_id=natural_body.attempt_id END$new$;
BEGIN
    FOREACH signature IN ARRAY ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
    ] LOOP
        definition := pg_get_functiondef(signature::regprocedure);
        arm_start := strpos(definition,start_marker);
        IF arm_start=0 OR strpos(substr(definition,arm_start+length(start_marker)),start_marker)>0 THEN
            RAISE EXCEPTION 'PIECE_NATURAL_RETRY_DEFINITION_CHANGED';
        END IF;
        arm_end := strpos(substr(definition,arm_start+length(start_marker)),end_marker);
        IF arm_end=0 THEN RAISE EXCEPTION 'PIECE_NATURAL_RETRY_DEFINITION_CHANGED'; END IF;
        arm_end := arm_start+length(start_marker)+arm_end-1;
        arm := substr(definition,arm_start,arm_end-arm_start);
        IF (length(arm)-length(replace(arm,old_attempts,'')))<>length(old_attempts)
           OR (length(arm)-length(replace(arm,old_author,'')))<>length(old_author) THEN
            RAISE EXCEPTION 'PIECE_NATURAL_RETRY_DEFINITION_CHANGED';
        END IF;
        EXECUTE substr(definition,1,arm_start-1)
            ||replace(replace(arm,old_attempts,new_attempts),old_author,new_author)
            ||substr(definition,arm_end);
    END LOOP;
END;
$migration$;
COMMIT;
