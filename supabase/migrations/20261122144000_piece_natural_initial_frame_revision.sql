-- Recognize the retained initial receipt after its first saved frame revision.
-- The selected answer and current receipt still use the locked live context.
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
    old_context text := $old$                        AND natural_body.payload->>'context_ref'=natural_context_ref$old$;
    new_context text := $new$                        AND (natural_body.id=natural_initial.id OR natural_body.payload->>'context_ref'=natural_context_ref)$new$;
    context_declaration text := '        natural_context_ref text;';
    live_feedback text := $marker$                    FROM jsonb_array_elements(current_context->'feedback') f),'[]'::jsonb) THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;$marker$;
    revision_check text := $check$
            IF initial_frame_event.id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(current_context->'feedback') f
                WHERE f->>'user_id'=p_owner_user_id::text
                  AND f->'frame_key'=initial_frame_event.payload#>'{frame_feedback_target,frame_key}'
                  AND f->'frame_ref'=initial_frame_event.payload#>'{frame_feedback_target,frame_ref}'
                  AND f->'source_emotion_id'=initial_frame_event.payload#>'{frame_feedback_target,input_id}'
                  AND f->>'status'='REVISED' AND f->'version'='1'::jsonb
                  AND natural_initial_finish.recorded_at<=(f->>'updated_at')::timestamptz
                  AND (f->>'updated_at')::timestamptz<=initial_frame_event.recorded_at
                  AND initial_frame_event.payload->>'request_fingerprint'='frame-feedback-request-'||encode(sha256(convert_to(
                      '['||(f->'frame_ref')::text||',"REVISED",'||(f->'correction_text')::text||']','UTF8')),'hex')
            ) THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;$check$;
    answer_time text := $marker$                BEGIN
                    natural_answer_at := (refined_payload->>'recorded_at')::timestamptz;$marker$;
    initial_check text := $check$                IF natural_initial.payload->>'context_ref' IS DISTINCT FROM natural_context_ref THEN
                    DECLARE
                        target jsonb;
                        prior_feedback_header text;
                        prior_context_ref text;
                    BEGIN
                        IF source_thread.issued_count IS DISTINCT FROM 1 OR tier IS DISTINCT FROM 'premium'
                           OR refined_answer.seq<>natural_initial_finish.seq+2 THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                        SELECT e.* INTO initial_frame_event FROM public.emlis_thread_events e
                            WHERE e.thread_id=source_thread.id AND e.seq=natural_initial_finish.seq+1 FOR SHARE OF e;
                        IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                        target := initial_frame_event.payload->'frame_feedback_target';
                        IF (initial_frame_event.kind='OPERATION' AND initial_frame_event.round_index=1
                            AND initial_frame_event.operation_id IS NULL AND initial_frame_event.attempt_id IS NULL
                            AND initial_frame_event.question_id IS NULL AND initial_frame_event.idempotency_key IS NOT NULL
                            AND natural_initial_finish.recorded_at<=initial_frame_event.recorded_at
                            AND initial_frame_event.recorded_at<=refined_answer.recorded_at
                            AND initial_frame_event.payload->>'status'='FRAME_REVISED'
                            AND initial_frame_event.payload-ARRAY['status','request_fingerprint','frame_feedback_target']='{}'::jsonb
                            AND jsonb_typeof(target)='object'
                            AND target ?& ARRAY['frame_key','frame_ref','input_id','feedback_version','source_guard',
                                'trigger','received_meaning','displayed_status','evidence_refs']
                            AND target-ARRAY['frame_key','frame_ref','input_id','feedback_version','source_guard',
                                'trigger','received_meaning','displayed_status','evidence_refs']='{}'::jsonb
                            AND target->'feedback_version'='1'::jsonb
                            AND target->>'displayed_status'='TENTATIVE'
                            AND jsonb_typeof(target->'source_guard')='array'
                            AND target#>>'{source_guard,0}'=target->>'input_id'
                            AND target->>'input_id'<>r.source_input_id
                            AND EXISTS (SELECT 1 FROM jsonb_array_elements(natural_guards) guard(value)
                                WHERE guard.value=target->'source_guard')
                            AND CASE WHEN jsonb_typeof(target->'evidence_refs')='array'
                                THEN jsonb_array_length(target->'evidence_refs')>0 ELSE false END
                            AND EXISTS (SELECT 1 FROM jsonb_array_elements(natural_feedback) feedback(value)
                                WHERE feedback.value=jsonb_build_array(target->'frame_key',1))
                            AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(
                                coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb)) dep
                                WHERE dep->>0=target->>'frame_key')
                        ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                        IF jsonb_typeof(natural_initial.payload#>'{artifact,interpretive_frames}') IS DISTINCT FROM 'array'
                           OR (SELECT count(*) FROM jsonb_array_elements(natural_initial.payload#>'{artifact,interpretive_frames}') frame
                                WHERE frame->'frame_key'=target->'frame_key'
                                  AND frame->'frame_ref'=target->'frame_ref'
                                  AND frame->'input_id'=target->'input_id'
                                  AND frame->'status'=target->'displayed_status'
                                  AND frame->'trigger'=target->'trigger'
                                  AND frame->'received_meaning'=target->'received_meaning'
                                  AND frame->'evidence_refs'=target->'evidence_refs')<>1 THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                        SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','||(x.value->1)::text||']',',' ORDER BY x.ordinality),'')||']'
                            INTO prior_feedback_header FROM jsonb_array_elements(natural_feedback) WITH ORDINALITY x(value,ordinality)
                            WHERE x.value<>jsonb_build_array(target->'frame_key',1);
                        prior_context_ref := 'context-'||encode(sha256(convert_to(
                            '['||to_jsonb(tier)::text||','||natural_guard_header||','||prior_feedback_header||']','UTF8')),'hex');
                        IF jsonb_array_length(coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb))>0 THEN
                            prior_context_ref := 'context-frame-targets-'||encode(sha256(convert_to(
                                '['||to_jsonb(prior_context_ref)::text||','||natural_target_tokens||']','UTF8')),'hex');
                        END IF;
                        IF natural_initial.payload->>'context_ref' IS DISTINCT FROM prior_context_ref THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                    END;
                END IF;
$check$;
BEGIN
    FOREACH signature IN ARRAY ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
    ] LOOP
        definition := pg_get_functiondef(signature::regprocedure);
        arm_start := strpos(definition,start_marker);
        IF arm_start=0 OR strpos(substr(definition,arm_start+length(start_marker)),start_marker)>0 THEN
            RAISE EXCEPTION 'PIECE_NATURAL_INITIAL_FRAME_DEFINITION_CHANGED';
        END IF;
        arm_end := strpos(substr(definition,arm_start+length(start_marker)),end_marker);
        IF arm_end=0 THEN RAISE EXCEPTION 'PIECE_NATURAL_INITIAL_FRAME_DEFINITION_CHANGED'; END IF;
        arm_end := arm_start+length(start_marker)+arm_end-1;
        arm := substr(definition,arm_start,arm_end-arm_start);
        IF (length(arm)-length(replace(arm,old_context,'')))<>length(old_context)
           OR (length(arm)-length(replace(arm,answer_time,'')))<>length(answer_time)
           OR (length(definition)-length(replace(definition,context_declaration,'')))<>length(context_declaration)
           OR (length(definition)-length(replace(definition,live_feedback,'')))<>length(live_feedback) THEN
            RAISE EXCEPTION 'PIECE_NATURAL_INITIAL_FRAME_DEFINITION_CHANGED';
        END IF;
        definition := substr(definition,1,arm_start-1)
            ||replace(replace(arm,old_context,new_context),answer_time,initial_check||answer_time)
            ||substr(definition,arm_end);
        -- The normal Q3 history and feedback locks are already held here.
        EXECUTE replace(replace(definition, context_declaration,
            context_declaration||E'\n        initial_frame_event public.emlis_thread_events%ROWTYPE;'),
            live_feedback, live_feedback||revision_check);
    END LOOP;
END;
$migration$;
COMMIT;
