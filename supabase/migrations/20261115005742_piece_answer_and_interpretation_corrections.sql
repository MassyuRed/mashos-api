-- Co-select the latest real answer and subsequent proper interpretation corrections.
-- Original rows, real answer checkpoints and correction receipts remain separate.
-- No new function, table, column, ACL, RLS, quota or public DTO key.
BEGIN;
DO $migration$
DECLARE signature text; definition text; old_text text; new_text text;
    constraint_name text; old_expression text;
BEGIN
    FOREACH constraint_name IN ARRAY ARRAY['piece_records_source_stage','piece_records_supplemental_boundary'] LOOP
        SELECT pg_get_constraintdef(c.oid) INTO definition FROM pg_constraint c
            WHERE c.conrelid='public.piece_records'::regclass AND c.conname=constraint_name;
        IF definition IS NULL OR definition NOT LIKE 'CHECK (%' THEN
            RAISE EXCEPTION 'PIECE_MIXED_SOURCE_PRECONDITION';
        END IF;
        old_expression:=substr(definition,8,length(definition)-8);
        EXECUTE format('ALTER TABLE public.piece_records DROP CONSTRAINT %I',constraint_name);
        EXECUTE format('ALTER TABLE public.piece_records ADD CONSTRAINT %I CHECK (((%s) OR (%s)) IS TRUE)',
            constraint_name,old_expression,$condition$source_lineage#>>'{observation,emlis_observation_stage}'='corrected_observation'
        AND source_lineage->'semantic_source_roles'='["original_input","supplemental_answer","interpretation_correction"]'::jsonb
        AND source_lineage->'lineage_control_roles'='["emlis_observation_result","question_need_decision","ai_interpretation_target"]'::jsonb
        AND jsonb_typeof(source_lineage#>'{observation,question_need_decision_identity}')='string'
        AND length(source_lineage#>>'{observation,question_need_decision_identity}')>0
        AND jsonb_typeof(source_lineage#>'{observation,supplemental_answer_identity}')='string'
        AND source_lineage#>>'{observation,supplemental_answer_identity}' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        AND source_lineage#>>'{observation,supplemental_answer_identity}'<>source_input_id::text
        AND source_lineage#>>'{observation,supplemental_answer_version}'='cocolon.cmee.supplemental_answer.v1'
        AND source_lineage#>>'{observation,supplemental_answer_bundle_commitment}' ~ '^sha256:[0-9a-f]{64}$'$condition$);
    END LOOP;
    FOREACH signature IN ARRAY ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
    ] LOOP
        definition:=pg_get_functiondef(signature::regprocedure);
        IF md5(definition) IS DISTINCT FROM (CASE signature
            WHEN 'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)' THEN 'd9ab63625133626efa4689cdf5ce7eb3'
            WHEN 'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)' THEN '03bf226132da62b32f2122729d0a4c88'
            WHEN 'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)' THEN 'abaec46041bc9d83e7430c147e849606'
            END) THEN RAISE EXCEPTION 'PIECE_MIXED_SOURCE_PRECONDITION'; END IF;
        old_text:=$old$        correction_history jsonb;$old$;
        new_text:=$new$        mixed_first_correction public.emlis_thread_events%ROWTYPE;
        mixed_answer_observation public.emlis_thread_events%ROWTYPE;
        mixed_answer_prefix text;
        correction_history jsonb;$new$;
        IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
            RAISE EXCEPTION 'PIECE_MIXED_SOURCE_PRECONDITION';
        END IF;
        definition:=replace(definition,old_text,new_text);
        old_text:=$old$                    IS DISTINCT FROM 'refined_observation'
                   AND source_thread.latest_answer_event_id IS NOT NULL)$old$;
        new_text:=$new$                    IS DISTINCT FROM 'refined_observation'
                   AND r.source_lineage#>>'{observation,emlis_observation_stage}' IS DISTINCT FROM 'corrected_observation'
                   AND source_thread.latest_answer_event_id IS NOT NULL)$new$;
        IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
            RAISE EXCEPTION 'PIECE_MIXED_SOURCE_PRECONDITION';
        END IF;
        definition:=replace(definition,old_text,new_text);
        old_text:=$old$                -- A real two-input correction is neither an ANSWER nor an
                -- INITIAL-only source. Lock the exact accepted source prefix.
                correction_expected := p_expected_source_state->'interpretation_correction';
                IF (jsonb_typeof(correction_expected)='object'
                    AND (NOT (correction_expected ? 'prior_sources')
                        OR (jsonb_typeof(correction_expected->'prior_sources')='array'
                            AND CASE WHEN jsonb_typeof(correction_expected->'prior_sources')='array' THEN jsonb_array_length(correction_expected->'prior_sources')>0 ELSE false END))) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_history := coalesce(correction_expected->'prior_sources','[]'::jsonb)
                    || jsonb_build_array(correction_expected->'source');
                correction_count := jsonb_array_length(correction_history);
                IF correction_count<1 OR (SELECT count(DISTINCT x.value->>'correction_id')
                    FROM jsonb_array_elements(correction_history) x(value))<>correction_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.id,e.payload->>'source_prefix_ref' INTO correction_previous_id,correction_base_prefix
                    FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                    AND e.kind='OBSERVATION' ORDER BY e.seq LIMIT 1;
                IF correction_previous_id IS NULL OR correction_base_prefix !~ '^emlis-q3-source-prefix-[0-9a-f]{64}$' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_previous_prefix := correction_base_prefix;
                correction_headers := '';
                FOR correction_source, correction_step IN SELECT value,ordinality::integer
                    FROM jsonb_array_elements(correction_history) WITH ORDINALITY LOOP
                IF (jsonb_typeof(correction_expected)='object'
                    AND correction_expected ?& ARRAY['source','source_prefix_ref','events','thread_data']
                    AND correction_expected-ARRAY['source','source_prefix_ref','events','thread_data','prior_sources']='{}'::jsonb
                    AND jsonb_typeof(correction_source)='object'
                    AND correction_source ?& ARRAY['correction_id','thread_id','original_source_ref',
                        'target_event_id','target_text','explanation','recorded_at','source_role']
                    AND correction_source-ARRAY['correction_id','thread_id','original_source_ref',
                        'target_event_id','target_text','explanation','recorded_at','source_role']='{}'::jsonb
                    AND correction_source->>'source_role'='USER_INTERPRETATION_CORRECTION'
                    AND correction_source->>'thread_id'=source_thread.id::text
                    AND correction_source->>'original_source_ref'=source_thread.data->>'original_source_ref'
                    AND correction_source->>'correction_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    AND correction_source->>'target_event_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    AND jsonb_typeof(correction_source->'explanation')='string'
                    AND length(btrim(correction_source->>'explanation')) BETWEEN 1 AND 2000
                    AND jsonb_typeof(correction_source->'target_text')='string'
                    AND length(btrim(correction_source->>'target_text')) BETWEEN 1 AND 2000
                    AND jsonb_typeof(correction_source->'recorded_at')='string'
                    AND jsonb_typeof(correction_expected->'events')='array'
                    AND correction_expected->'thread_data'=source_thread.data
                    AND correction_expected->>'source_prefix_ref'=source_thread.source_prefix_ref
                    AND source_thread.source_prefix_ref ~ '^emlis-corrected-source-prefix-[0-9a-f]{64}$'
                    AND source_thread.data->>'runtime_profile'='q3.plan.sequential.v1'
                    AND source_thread.data->>'response_profile'='natural_reply.v1'
                    AND source_thread.state='COMPLETED' AND source_thread.issued_count=0
                    AND source_thread.latest_answer_event_id IS NULL
                    AND source_thread.current_meaning_event_id IS NULL
                    AND source_thread.evaluated_prefix_ref IS NULL
                    AND source_thread.active_operation_id IS NULL
                    AND source_thread.active_attempt_id IS NULL
                    AND source_thread.processing_deadline_at IS NULL
                    AND source_thread.data->>'body_state'='FINAL'
                    AND source_thread.data->>'natural_response_stage'='FINAL'
                    AND source_thread.data->>'answer_assessment'='NOT_APPLICABLE'
                    AND source_thread.data->>'failure_code' IS NULL
                    AND source_thread.data->>'semantic_profile' IS NULL
                    AND (source_thread.data->'meaning_updated' IS NULL
                        OR source_thread.data->'meaning_updated' IN ('null'::jsonb,'false'::jsonb))
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                PERFORM 1 FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id ORDER BY e.seq FOR SHARE OF e;
                SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.seq),'[]'::jsonb)
                    INTO correction_events FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id;
                IF correction_events IS DISTINCT FROM correction_expected->'events'
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind IN ('QUESTION','ANSWER','MEANING_UPDATE','TERMINAL'))<>0
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OBSERVATION')<>correction_count+1
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.payload->>'stage'='INTERPRETATION_CORRECTION')<>correction_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO correction_event FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage'='INTERPRETATION_CORRECTION'
                      AND e.id::text=correction_source->>'correction_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_target FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.id::text=correction_source->>'target_event_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_body FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION'
                      AND e.operation_id=correction_event.operation_id AND e.attempt_id=correction_event.attempt_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (correction_event.id::text=correction_source->>'correction_id'
                    AND correction_event.round_index=0 AND correction_event.question_id IS NULL
                    AND correction_event.payload->'source'=correction_source
                    AND correction_event.payload->>'status'='SAVED'
                    AND correction_event.payload->>'assessment'='UNASSESSED'
                    AND correction_event.idempotency_key IS NOT NULL
                    AND correction_event.operation_id IS NOT NULL AND correction_event.attempt_id IS NOT NULL
                    AND correction_target.kind='OBSERVATION' AND correction_target.round_index=0
                    AND correction_target.id=correction_previous_id
                    AND correction_target.payload->>'stage'=CASE WHEN correction_step=1 THEN 'INITIAL' ELSE 'CORRECTED' END
                    AND correction_target.payload->>'source_prefix_ref'=correction_previous_prefix
                    AND correction_target.payload->>'source_prefix_ref'<>source_thread.source_prefix_ref
                    AND correction_body.kind='OBSERVATION' AND correction_body.round_index=0
                    AND correction_body.payload->>'stage'='CORRECTED'
                    AND (correction_step<>correction_count OR (correction_body.id=source_thread.last_observation_event_id
                        AND correction_body.payload->>'source_prefix_ref'=source_thread.source_prefix_ref))
                    AND correction_body.operation_id=correction_event.operation_id
                    AND correction_body.attempt_id=correction_event.attempt_id
                    AND (correction_step<>correction_count OR (
                        correction_body.operation_id::text=source_thread.data->>'operation_id'
                        AND correction_body.attempt_id::text=source_thread.data->>'attempt_id'))
                    AND correction_target.seq<correction_event.seq AND correction_event.seq<correction_body.seq
                    AND correction_target.recorded_at<=(correction_source->>'recorded_at')::timestamptz
                    AND correction_target.recorded_at<=correction_event.recorded_at
                    AND (correction_source->>'recorded_at')::timestamptz<=correction_event.recorded_at
                    AND correction_event.recorded_at<=correction_body.recorded_at
                    AND correction_body.recorded_at<=clock_timestamp()
                    AND NOT (correction_target.payload ? 'meaning_checkpoint_ref')
                    AND NOT (correction_body.payload ? 'meaning_checkpoint_ref')
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                correction_excerpt := correction_source->>'target_text';
                correction_target_text := correction_target.payload->>'text';
                correction_excerpt_at := strpos(correction_target_text,correction_excerpt);
                IF correction_excerpt_at<1 OR strpos(substr(correction_target_text,
                    correction_excerpt_at+1),correction_excerpt)>0 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                -- Exact compact metadata, with no normalization of either
                -- explanation or quoted AI locator. The separate raw frame
                -- contains only the person's explanation as evidence text.
                correction_header := '{"correction_id":'||(correction_source->'correction_id')::text
                    ||',"explanation":'||(correction_source->'explanation')::text
                    ||',"original_source_ref":'||(correction_source->'original_source_ref')::text
                    ||',"recorded_at":'||(correction_source->'recorded_at')::text
                    ||',"source_role":'||(correction_source->'source_role')::text
                    ||',"target_event_id":'||(correction_source->'target_event_id')::text
                    ||',"target_text":'||(correction_source->'target_text')::text
                    ||',"thread_id":'||(correction_source->'thread_id')::text||'}';
                -- Each historical prefix is BASE + the full ordered history
                -- through this source, never a recursive corrected-prefix hash.
                correction_headers := correction_headers || CASE WHEN correction_step=1 THEN '' ELSE ',' END || correction_header;
                correction_prefix := 'emlis-corrected-source-prefix-'||encode(sha256(convert_to(
                    '['||to_jsonb(correction_base_prefix)::text||',['||correction_headers||']]','UTF8')),'hex');
                IF correction_body.payload->>'source_prefix_ref' IS DISTINCT FROM correction_prefix
                    OR (correction_step=correction_count AND source_thread.source_prefix_ref IS DISTINCT FROM correction_prefix) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_frame := 'memo:'||octet_length(convert_to(correction_source->>'explanation','UTF8'))::text
                    ||':'||(correction_source->>'explanation')||'memo_action:0:';
                IF correction_step=correction_count AND (r.source_lineage#>>'{interpretation_correction_source,correction_id}'=correction_event.id::text
                    AND r.source_lineage#>>'{interpretation_correction_source,target_event_id}'=correction_target.id::text
                    AND r.source_lineage#>>'{interpretation_correction_source,source_version}'=
                        'sha256:'||encode(sha256(convert_to(correction_header,'UTF8')),'hex')
                    AND r.source_lineage#>>'{interpretation_correction_source,explanation_commitment}'=
                        'sha256:'||encode(sha256(convert_to(correction_frame,'UTF8')),'hex')
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                -- Exact compact array serialization of the existing identity(
                -- 'context', tier, guards, feedback); only typed scalar arrays
                -- enter this digest, so no whitespace is removed from strings.
                natural_guards := coalesce(source_thread.data->'context_guards','[]'::jsonb);
                natural_feedback := coalesce(source_thread.data->'context_feedback','[]'::jsonb);
                IF jsonb_typeof(natural_guards) IS DISTINCT FROM 'array'
                   OR jsonb_typeof(natural_feedback) IS DISTINCT FROM 'array' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF EXISTS (SELECT 1 FROM jsonb_array_elements(natural_guards) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>3
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->2) IS DISTINCT FROM 'number'
                          OR (x.value->>2) !~ '^(0|[1-9][0-9]*)$' END)
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(natural_feedback) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>2
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'number'
                          OR (x.value->>1) !~ '^(0|[1-9][0-9]*)$' END) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||','||(x.value->2)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_guard_header
                    FROM jsonb_array_elements(natural_guards) WITH ORDINALITY x(value,ordinality);
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_feedback_header
                    FROM jsonb_array_elements(natural_feedback) WITH ORDINALITY x(value,ordinality);
                natural_context_ref := 'context-'||encode(sha256(convert_to(
                    '['||to_jsonb(tier)::text||','||natural_guard_header||','||natural_feedback_header||']',
                    'UTF8')),'hex');
                IF jsonb_array_length(coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb))>0 THEN
                    SELECT '['||coalesce(string_agg(to_jsonb(
                        (x.value->>0)||':'||(x.value->>1)||':'||(x.value->>2)||':'||
                        (x.value->>3)||':'||(x.value->>4)||':'||(x.value->>5))::text,
                        ',' ORDER BY x.ordinality),'')||']' INTO natural_target_tokens
                        FROM jsonb_array_elements(source_thread.data->'frame_target_dependencies') WITH ORDINALITY x(value,ordinality);
                    natural_context_ref := 'context-frame-targets-'||encode(sha256(convert_to(
                        '['||to_jsonb(natural_context_ref)::text||','||natural_target_tokens||']','UTF8')),'hex');
                END IF;
                -- Same receipt and completion checks as the natural arm,
                -- with FINAL response_stage and no fictitious question/checkpoint.
                FOR natural_body IN SELECT e.* FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id
                      AND e.id IN (correction_target.id,correction_body.id) ORDER BY e.seq LOOP
                    natural_prefix := natural_body.payload->>'source_prefix_ref';
                    IF (natural_body.operation_id IS NOT NULL AND natural_body.attempt_id IS NOT NULL
                        AND natural_body.question_id IS NULL
                        AND natural_body.payload->>'context_ref'=natural_context_ref
                        AND natural_body.payload->'context_guards'=natural_guards
                        AND jsonb_typeof(natural_body.payload->'text')='string'
                        AND length(btrim(natural_body.payload->>'text'))>0
                        AND natural_body.payload#>>'{artifact,schema_version}'='cocolon.emlis.recipient_reply.v1'
                        AND natural_body.payload#>'{artifact,text}'=natural_body.payload->'text'
                        AND jsonb_typeof(natural_body.payload#>'{artifact,model}')='string'
                        AND length(btrim(natural_body.payload#>>'{artifact,model}'))>0
                        AND public.piece_natural_analysis_artifact_valid(natural_body.payload->'artifact',
                            natural_prefix,source_thread.user_id,source_thread.source_snapshot)
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED')<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED')<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'status'='COMPLETED'
                        AND e.payload->>'failure_code' IS NULL)<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT e.* INTO natural_started FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED';
                    SELECT e.* INTO natural_received FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED';
                    SELECT e.* INTO correction_finish FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'status'='COMPLETED' AND e.payload->>'failure_code' IS NULL;
                    IF (natural_started.round_index=0 AND natural_received.round_index=0
                        AND correction_finish.round_index=0 AND natural_body.round_index=0
                        AND natural_started.payload->>'source_prefix_ref'=natural_prefix
                        AND natural_received.payload->>'source_prefix_ref'=natural_prefix
                        AND natural_started.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_received.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_started.payload->>'response_stage'='FINAL'
                        AND natural_received.payload->>'response_stage'='FINAL'
                        AND natural_received.payload->'reply'=jsonb_build_object('text',natural_body.payload->'text',
                            'model',natural_body.payload#>'{artifact,model}','source_prefix_ref',natural_prefix,
                            'schema_version','cocolon.emlis.recipient_reply.v1')
                        AND natural_started.seq<natural_received.seq AND natural_received.seq<natural_body.seq
                        AND natural_body.seq<correction_finish.seq
                        AND source_created AT TIME ZONE 'UTC'<=natural_started.recorded_at
                        AND natural_started.recorded_at<=natural_received.recorded_at
                        AND natural_received.recorded_at<=natural_body.recorded_at
                        AND natural_body.recorded_at<=correction_finish.recorded_at
                        AND correction_finish.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF natural_body.id=correction_target.id THEN
                        IF correction_finish.seq>=correction_event.seq
                           OR correction_finish.recorded_at>(correction_source->>'recorded_at')::timestamptz THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                    ELSIF correction_event.seq>=natural_started.seq
                       OR correction_event.recorded_at>natural_started.recorded_at THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END LOOP;
                correction_previous_id := correction_body.id;
                correction_previous_prefix := correction_prefix;
                END LOOP;
$old$;
        new_text:=$new$                IF source_thread.latest_answer_event_id IS NOT NULL THEN
                -- A real two-input correction is neither an ANSWER nor an
                -- INITIAL-only source. Lock the exact accepted source prefix.
                correction_expected := p_expected_source_state->'interpretation_correction';
                IF (jsonb_typeof(correction_expected)='object'
                    AND (NOT (correction_expected ? 'prior_sources')
                        OR (jsonb_typeof(correction_expected->'prior_sources')='array'
                            AND CASE WHEN jsonb_typeof(correction_expected->'prior_sources')='array' THEN jsonb_array_length(correction_expected->'prior_sources')>0 ELSE false END))) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_history := coalesce(correction_expected->'prior_sources','[]'::jsonb)
                    || jsonb_build_array(correction_expected->'source');
                correction_count := jsonb_array_length(correction_history);
                IF correction_count<1 OR (SELECT count(DISTINCT x.value->>'correction_id')
                    FROM jsonb_array_elements(correction_history) x(value))<>correction_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF (CASE WHEN jsonb_typeof(correction_expected->'answer_sources')='array'
                        AND jsonb_typeof(correction_expected->'answer_checkpoints')='array' THEN
                    jsonb_array_length(correction_expected->'answer_sources')=source_thread.issued_count
                    AND jsonb_array_length(correction_expected->'answer_checkpoints')=source_thread.issued_count
                    ELSE false END) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO mixed_first_correction FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                    AND e.payload->>'stage'='INTERPRETATION_CORRECTION' ORDER BY e.seq LIMIT 1 FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                    AND e.kind='OBSERVATION' AND e.round_index=source_thread.issued_count
                    AND e.payload->>'stage'='REFINED')<>1 THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO mixed_answer_observation FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION'
                    AND e.round_index=source_thread.issued_count AND e.payload->>'stage'='REFINED' FOR SHARE OF e;
                mixed_answer_prefix:=mixed_answer_observation.payload->>'source_prefix_ref';
                -- The existing original/profile/thread locks remain held.
                -- Read the committed answer, decision, checkpoint and result;
                -- none of their generated prose becomes Piece source material.
                IF source_thread.state IS DISTINCT FROM 'COMPLETED'
                   OR source_thread.active_attempt_id IS NOT NULL
                   OR source_thread.processing_deadline_at IS NOT NULL
                   OR source_thread.latest_answer_event_id::text IS DISTINCT FROM
                        r.source_lineage#>>'{observation,supplemental_answer_identity}'
                   OR source_thread.issued_count NOT IN (1,2,3)
                   OR source_thread.data->>'runtime_profile' IS DISTINCT FROM 'q3.plan.sequential.v1'
                   OR source_thread.data->>'response_profile' IS DISTINCT FROM 'natural_reply.v1'
                   OR source_thread.data->>'natural_question_policy' IS DISTINCT FROM 'native_bound_question.v1'
                   OR NOT coalesce(source_thread.data->>'analysis_state' IN ('GENERATED','NOT_GENERATED'),false)
                   OR (source_thread.data->>'analysis_state'='GENERATED'
                       AND source_thread.data->>'natural_meaning_profile' IS DISTINCT FROM 'source_grounded_active_meaning.v1')
                   OR source_thread.data->>'natural_response_stage' IS DISTINCT FROM 'FINAL'
                   OR source_thread.data->>'semantic_profile' IS NOT NULL
                   OR source_thread.data->>'body_state' IS DISTINCT FROM 'FINAL'
                   OR source_thread.data->>'answer_assessment' IS DISTINCT FROM 'RESOLVED'
                   OR source_thread.data->'meaning_updated' IS DISTINCT FROM 'false'::jsonb
                   OR source_thread.data->>'failure_code' IS NOT NULL THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='ANSWER')<>source_thread.issued_count
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='QUESTION')<>source_thread.issued_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO refined_answer FROM public.emlis_thread_events e
                    WHERE e.id=source_thread.latest_answer_event_id AND e.thread_id=source_thread.id
                    FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO refined_question FROM public.emlis_thread_events e
                    WHERE e.id::text=r.source_lineage#>>'{observation,question_need_decision_identity}'
                      AND e.thread_id=source_thread.id FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO refined_checkpoint FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='MEANING_UPDATE' AND e.round_index=source_thread.issued_count
                    FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO refined_observation FROM public.emlis_thread_events e
                    WHERE e.id=mixed_answer_observation.id AND e.thread_id=source_thread.id
                    FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                refined_payload := refined_answer.payload->'source';
                IF (jsonb_typeof(refined_payload)='object'
                    AND refined_payload ?& ARRAY['answer_id','thread_id','question_id','round_index',
                        'original_source_ref','answer_text_private','recorded_at','authored_at',
                        'source_version','source_role']
                    AND refined_payload-ARRAY['answer_id','thread_id','question_id','round_index',
                        'original_source_ref','answer_text_private','recorded_at','authored_at',
                        'source_version','source_role']='{}'::jsonb
                    AND refined_answer.kind='ANSWER' AND refined_answer.round_index=source_thread.issued_count
                    AND refined_payload->>'answer_id'=refined_answer.id::text
                    AND refined_payload->>'thread_id'=source_thread.id::text
                    AND refined_payload->'round_index'=to_jsonb(source_thread.issued_count)
                    AND refined_payload->>'source_role'='SUPPLEMENTAL_ANSWER'
                    AND refined_payload->>'source_version'='cocolon.cmee.supplemental_answer.v1'
                    AND refined_payload->>'source_version'=
                        r.source_lineage#>>'{observation,supplemental_answer_version}'
                    AND refined_payload->>'original_source_ref'=source_thread.data->>'original_source_ref'
                    AND jsonb_typeof(refined_payload->'answer_text_private')='string'
                    AND length(btrim(refined_payload->>'answer_text_private'))>0
                    AND jsonb_typeof(refined_payload->'recorded_at')='string'
                    AND jsonb_typeof(refined_payload->'authored_at') IN ('string','null')
                    AND refined_question.kind='QUESTION' AND refined_question.round_index=source_thread.issued_count
                    AND refined_question.question_id=refined_answer.question_id
                    AND refined_payload->>'question_id'=refined_question.question_id
                    AND refined_question.payload->>'question_id'=refined_question.question_id
                    AND refined_question.payload->>'thread_id'=source_thread.id::text
                    AND refined_question.payload->>'schema_version'='cocolon.cmee.emlis_clarification.v1'
                    AND refined_question.payload#>>'{decision,disposition}'='ASK'
                    AND refined_question.payload->>'original_source_ref'=refined_payload->>'original_source_ref'
                    AND refined_question.seq<refined_answer.seq
                    AND refined_answer.seq<refined_checkpoint.seq
                    AND refined_checkpoint.seq<refined_observation.seq
                    AND refined_checkpoint.kind='MEANING_UPDATE'
                    AND refined_checkpoint.payload->>'semantic_schema_version'='cocolon.cmee.emlis_answer_meaning.v1'
                    AND refined_checkpoint.payload->>'source_prefix_ref'=mixed_answer_prefix
                    AND refined_checkpoint.payload->>'assessment_status'='RESOLVED'
                    AND refined_checkpoint.payload->'unresolved_parts'='[]'::jsonb
                    AND refined_observation.kind='OBSERVATION' AND refined_observation.round_index=source_thread.issued_count
                    AND refined_observation.payload->>'stage'='REFINED'
                    AND refined_observation.payload->>'source_prefix_ref'=mixed_answer_prefix
                    AND NOT (refined_observation.payload ? 'meaning_checkpoint_ref')
                    AND refined_answer.operation_id=refined_observation.operation_id
                    AND refined_answer.attempt_id=refined_observation.attempt_id
                    AND refined_checkpoint.operation_id=refined_observation.operation_id
                    AND refined_checkpoint.attempt_id=refined_observation.attempt_id
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                refined_update := refined_checkpoint.payload->'answer_update';
                IF (jsonb_typeof(refined_update)='object'
                    AND refined_update->>'disposition'='MATERIAL_UPDATE'
                    AND refined_update->>'question_ref'=refined_question.question_id
                    AND refined_update->'unresolved_parts'='[]'::jsonb
                    AND jsonb_typeof(refined_update->'updates')='array'
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF true THEN
                    IF (CASE WHEN jsonb_typeof(correction_expected->'answer_checkpoints')='array' THEN
                        source_thread.issued_count IN (1,2,3)
                        AND NOT (false)
                        AND jsonb_array_length(correction_expected->'answer_checkpoints')=source_thread.issued_count
                        AND correction_expected->'answer_checkpoints'->(source_thread.issued_count-1)=refined_checkpoint.payload
                    ELSE false END) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                ELSE
                IF false
                    AND 'null'::jsonb IS DISTINCT FROM refined_checkpoint.payload THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF (jsonb_array_length(refined_update->'updates')>=1 AND NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements(refined_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                )) IS NOT TRUE THEN
                    -- Only the selected latest exact-clause checkpoint is extended.
                    -- Earlier rounds below still require the unchanged ADD chain.
                    IF (source_thread.issued_count IN (1,2,3)
                        AND 'null'::jsonb=refined_checkpoint.payload
                        AND jsonb_array_length(refined_update->'updates')=1
                        AND jsonb_typeof(refined_checkpoint.payload->'inactive_claim_refs')='array'
                        AND EXISTS (
                            SELECT 1 FROM jsonb_array_elements(refined_update->'updates') item
                            WHERE CASE WHEN jsonb_typeof(item)='object'
                                AND jsonb_typeof(item->'target_meaning_refs')='array'
                                AND jsonb_typeof(item->'superseded_claim_refs')='array'
                                AND jsonb_typeof(item->'changed_claim_refs')='array'
                                AND jsonb_typeof(item->'affected_dependency_refs')='array'
                                AND jsonb_typeof(item->'evidence_refs')='array'
                                AND jsonb_typeof(refined_checkpoint.payload->'inactive_claim_refs')='array'
                            THEN item->>'operation' IN ('REVISE','WITHDRAW')
                                AND item->>'binding_kind'='EXPLICIT_CORRECTION'
                                AND item#>>'{temporal_binding,about_time}'='ORIGINAL_OCCASION'
                                AND item#>>'{temporal_binding,anchor_source_ref}'=source_thread.data->>'original_source_ref'
                                AND item#>'{temporal_binding,time_expression_evidence_refs}'='[]'::jsonb
                                AND jsonb_array_length(item->'target_meaning_refs')=1
                                AND item#>>'{target_meaning_refs,0}' ~ '^nucleus:s[0-9]+$'
                                AND item->'superseded_claim_refs'=item->'target_meaning_refs'
                                AND jsonb_array_length(item->'evidence_refs')=1
                                AND item#>>'{evidence_refs,0}' ~ '^ev-[0-9a-f]{24}$'
                                AND item->>'update_ref' ~ '^emlis-update-[0-9a-f]{64}$'
                                AND refined_checkpoint.payload->'accepted_update_refs'=(
                                    SELECT coalesce(jsonb_agg(to_jsonb(ref) ORDER BY seq,ordinal),'[]'::jsonb)
                                    FROM (
                                        SELECT DISTINCT ON (entry->>'update_ref') entry->>'update_ref' AS ref,e.seq,ordinal
                                        FROM public.emlis_thread_events e
                                        CROSS JOIN LATERAL jsonb_array_elements(e.payload#>'{answer_update,updates}')
                                            WITH ORDINALITY AS updates(entry,ordinal)
                                        WHERE e.thread_id=source_thread.id AND e.kind='MEANING_UPDATE'
                                            AND e.round_index BETWEEN 1 AND source_thread.issued_count
                                        ORDER BY entry->>'update_ref',e.seq,ordinal
                                    ) accepted
                                )
                                AND NOT EXISTS (
                                    SELECT 1 FROM jsonb_array_elements(item->'affected_dependency_refs') dependency
                                    WHERE (jsonb_typeof(dependency)='string'
                                        AND dependency#>>'{}' ~ '^relation:r[0-9]+$') IS NOT TRUE)
                                AND (SELECT array_agg(value ORDER BY value)
                                    FROM jsonb_array_elements_text(refined_checkpoint.payload->'inactive_claim_refs'))
                                    = (SELECT array_agg(value ORDER BY value)
                                    FROM jsonb_array_elements_text((item->'superseded_claim_refs')||(item->'affected_dependency_refs')))
                                AND ((item->>'operation'='REVISE'
                                    AND jsonb_array_length(item->'changed_claim_refs')=1
                                    AND item#>>'{changed_claim_refs,0}' ~ '^answer:s[0-9]+$')
                                    OR (item->>'operation'='WITHDRAW' AND item->'changed_claim_refs'='[]'::jsonb))
                            ELSE false END
                        )
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                END IF;
                -- Exact compact, lexically sorted metadata JSON of the existing
                -- freeze_supplemental_answer owner. Byte length is UTF-8 length,
                -- not character count; text is not normalized or concatenated
                -- into the saved original. The resulting digest includes every
                -- answer identity/version/time/parent field and the exact body.
                END IF;
                refined_header := '{"answer_id":'||(refined_payload->'answer_id')::text
                    ||',"authored_at":'||(refined_payload->'authored_at')::text
                    ||',"original_source_ref":'||(refined_payload->'original_source_ref')::text
                    ||',"question_id":'||(refined_payload->'question_id')::text
                    ||',"recorded_at":'||(refined_payload->'recorded_at')::text
                    ||',"round_index":'||(refined_payload->'round_index')::text
                    ||',"source_role":'||(refined_payload->'source_role')::text
                    ||',"source_version":'||(refined_payload->'source_version')::text
                    ||',"thread_id":'||(refined_payload->'thread_id')::text||'}';
                refined_frame_hash := encode(sha256(convert_to(
                    E'CMEE_EMLIS_ANSWER_FRAME_UTF8_V1\n'||refined_header
                    ||E'\n@answer_text_private:'||octet_length(refined_payload->>'answer_text_private')::text
                    ||E'\n'||(refined_payload->>'answer_text_private'),'UTF8')),'hex');
                IF 'sha256:'||refined_frame_hash IS DISTINCT FROM
                    r.source_lineage#>>'{observation,supplemental_answer_bundle_commitment}' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                refined_envelope_ref := 'src-'||substr(encode(sha256(convert_to(
                    '{"label_contract_digest":"","label_contract_id":"","raw_sha256":"'
                    ||refined_frame_hash||'","schema":"cocolon.cmee.source_envelope.identity.v2",'
                    ||'"source_contract_version":"cocolon.cmee.emlis_thread.v1",'
                    ||'"source_encoding":"CMEE_EMLIS_ANSWER_FRAME_UTF8_V1","source_record_id":'
                    ||(refined_payload->'answer_id')::text
                    ||',"source_role":"SUPPLEMENTAL_ANSWER","source_schema_version":"cocolon.cmee.supplemental_answer.v1"}',
                    'UTF8')),'hex'),1,24);
                IF refined_update->>'answer_source_ref' IS DISTINCT FROM refined_envelope_ref THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                -- Natural replies have no initial semantic checkpoint and no
                -- synthetic meaning_checkpoint_ref on either OBSERVATION.
                IF (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='MEANING_UPDATE')<>source_thread.issued_count
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION')<>source_thread.issued_count+correction_count+1
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage' IN ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'))<>2*(source_thread.issued_count+correction_count+1)
                   OR refined_checkpoint.round_index IS DISTINCT FROM source_thread.issued_count
                   OR jsonb_typeof(refined_checkpoint.payload->'checkpoint_id') IS DISTINCT FROM 'string'
                   OR length(coalesce(refined_checkpoint.payload->>'checkpoint_id',''))=0 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO natural_first_question FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='QUESTION' AND e.round_index=1 FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO natural_initial FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION'
                      AND e.round_index=0 AND e.payload->>'stage'='INITIAL' FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (natural_initial.seq<natural_first_question.seq
                    AND natural_initial.operation_id IS NOT NULL AND natural_initial.attempt_id IS NOT NULL
                    AND natural_first_question.operation_id=natural_initial.operation_id
                    AND natural_first_question.attempt_id=natural_initial.attempt_id
                    AND natural_initial.payload->>'source_prefix_ref'<>mixed_answer_prefix
                    AND NOT (natural_initial.payload ? 'meaning_checkpoint_ref')
                    AND natural_initial.recorded_at<=natural_first_question.recorded_at
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                -- Exact compact array serialization of the existing identity(
                -- 'context', tier, guards, feedback); only typed scalar arrays
                -- enter this digest, so no whitespace is removed from strings.
                natural_guards := coalesce(source_thread.data->'context_guards','[]'::jsonb);
                natural_feedback := coalesce(source_thread.data->'context_feedback','[]'::jsonb);
                IF jsonb_typeof(natural_guards) IS DISTINCT FROM 'array'
                   OR jsonb_typeof(natural_feedback) IS DISTINCT FROM 'array' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF EXISTS (SELECT 1 FROM jsonb_array_elements(natural_guards) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>3
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->2) IS DISTINCT FROM 'number'
                          OR (x.value->>2) !~ '^(0|[1-9][0-9]*)$' END)
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(natural_feedback) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>2
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'number'
                          OR (x.value->>1) !~ '^(0|[1-9][0-9]*)$' END) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||','||(x.value->2)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_guard_header
                    FROM jsonb_array_elements(natural_guards) WITH ORDINALITY x(value,ordinality);
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_feedback_header
                    FROM jsonb_array_elements(natural_feedback) WITH ORDINALITY x(value,ordinality);
                natural_context_ref := 'context-'||encode(sha256(convert_to(
                    '['||to_jsonb(tier)::text||','||natural_guard_header||','||natural_feedback_header||']',
                    'UTF8')),'hex');
                IF jsonb_array_length(coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb))>0 THEN
                    SELECT '['||coalesce(string_agg(to_jsonb(
                        (x.value->>0)||':'||(x.value->>1)||':'||(x.value->>2)||':'||
                        (x.value->>3)||':'||(x.value->>4)||':'||(x.value->>5))::text,
                        ',' ORDER BY x.ordinality),'')||']' INTO natural_target_tokens
                        FROM jsonb_array_elements(source_thread.data->'frame_target_dependencies') WITH ORDINALITY x(value,ordinality);
                    natural_context_ref := 'context-frame-targets-'||encode(sha256(convert_to(
                        '['||to_jsonb(natural_context_ref)::text||','||natural_target_tokens||']','UTF8')),'hex');
                END IF;
                IF refined_observation.payload->>'context_ref' IS DISTINCT FROM natural_context_ref
                   OR refined_observation.payload->'context_guards' IS DISTINCT FROM natural_guards THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                FOR natural_body IN SELECT e.* FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id
                      AND e.id IN (natural_initial.id,refined_observation.id) ORDER BY e.seq
                    FOR SHARE OF e
                LOOP
                    natural_response_stage := CASE WHEN natural_body.id=natural_initial.id
                        THEN 'PRE_QUESTION' ELSE 'REFINED' END;
                    natural_prefix := natural_body.payload->>'source_prefix_ref';
                    IF (natural_body.operation_id IS NOT NULL AND natural_body.attempt_id IS NOT NULL
                        AND jsonb_typeof(natural_body.payload->'source_prefix_ref')='string'
                        AND length(natural_prefix)>0 AND natural_prefix !~ '[[:space:]]'
                        AND jsonb_typeof(natural_body.payload->'context_ref')='string'
                        AND length(natural_body.payload->>'context_ref')>0
                        AND natural_body.payload->>'context_ref' !~ '[[:space:]]'
                        AND natural_body.payload->>'context_ref'=natural_context_ref
                        AND natural_body.payload->'context_guards'=natural_guards
                        AND jsonb_typeof(natural_body.payload->'text')='string'
                        AND length(btrim(natural_body.payload->>'text'))>0
                        AND jsonb_typeof(natural_body.payload->'artifact')='object'
                        AND natural_body.payload#>>'{artifact,schema_version}'='cocolon.emlis.recipient_reply.v1'
                        AND public.piece_natural_analysis_artifact_valid(
                            natural_body.payload->'artifact',natural_prefix,
                            source_thread.user_id,source_thread.source_snapshot)
                        AND natural_body.payload#>'{artifact,text}'=natural_body.payload->'text'
                        AND jsonb_typeof(natural_body.payload#>'{artifact,model}')='string'
                        AND length(btrim(natural_body.payload#>>'{artifact,model}'))>0
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF (SELECT count(*) FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                          AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED'
                          AND e.payload->>'source_prefix_ref'=natural_prefix)<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                          AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED'
                          AND e.payload->>'source_prefix_ref'=natural_prefix)<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT e.* INTO natural_started FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                          AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED'
                          AND e.payload->>'source_prefix_ref'=natural_prefix FOR SHARE OF e;
                    SELECT e.* INTO natural_received FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                          AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED'
                          AND e.payload->>'source_prefix_ref'=natural_prefix FOR SHARE OF e;
                    IF (natural_started.operation_id=natural_body.operation_id
                        AND natural_received.operation_id=natural_body.operation_id
                        AND natural_started.attempt_id=natural_body.attempt_id
                        AND natural_received.attempt_id=natural_body.attempt_id
                        AND natural_started.round_index=natural_body.round_index
                        AND natural_received.round_index=natural_body.round_index
                        AND natural_started.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_received.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_started.payload->>'response_stage'=natural_response_stage
                        AND natural_received.payload->>'response_stage'=natural_response_stage
                        AND natural_received.payload->'reply'=jsonb_build_object(
                            'text',natural_body.payload->'text',
                            'model',natural_body.payload#>'{artifact,model}',
                            'source_prefix_ref',natural_prefix,
                            'schema_version','cocolon.emlis.recipient_reply.v1')
                        AND natural_started.seq<natural_received.seq
                        AND natural_received.seq<natural_body.seq
                        AND source_created AT TIME ZONE 'UTC'<=natural_started.recorded_at
                        AND natural_started.recorded_at<=natural_received.recorded_at
                        AND natural_received.recorded_at<=natural_body.recorded_at
                        AND natural_body.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF natural_body.id=refined_observation.id AND (
                        refined_checkpoint.seq>=natural_started.seq
                        OR refined_checkpoint.recorded_at>natural_started.recorded_at) THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END LOOP;
                IF (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.operation_id=natural_initial.operation_id AND e.attempt_id=natural_initial.attempt_id
                      AND e.payload->>'status'='AWAITING_ANSWER' AND e.payload->>'failure_code' IS NULL)<>1 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO natural_initial_finish FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.operation_id=natural_initial.operation_id AND e.attempt_id=natural_initial.attempt_id
                      AND e.payload->>'status'='AWAITING_ANSWER' AND e.payload->>'failure_code' IS NULL
                    FOR SHARE OF e;
                IF (natural_first_question.seq<natural_initial_finish.seq
                    AND natural_initial_finish.seq<refined_answer.seq
                    AND natural_initial_finish.round_index=1
                    AND natural_first_question.recorded_at<=natural_initial_finish.recorded_at
                    AND natural_initial_finish.recorded_at<=refined_answer.recorded_at
                    AND refined_answer.recorded_at<=refined_checkpoint.recorded_at
                    AND refined_observation.operation_id IS NOT NULL AND refined_observation.attempt_id IS NOT NULL
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                BEGIN
                    natural_answer_at := (refined_payload->>'recorded_at')::timestamptz;
                EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END;
                IF (natural_initial_finish.recorded_at<=natural_answer_at
                    AND natural_answer_at<=refined_answer.recorded_at) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF source_thread.data ? 'continuation_question'
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.operation_id=refined_observation.operation_id AND e.attempt_id=refined_observation.attempt_id
                      AND e.payload->>'status' IN ('COMPLETED','AWAITING_CONTINUE')
                      AND e.payload->>'failure_code' IS NULL)<>1 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO natural_finish FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.operation_id=refined_observation.operation_id AND e.attempt_id=refined_observation.attempt_id
                      AND e.payload->>'status' IN ('COMPLETED','AWAITING_CONTINUE')
                      AND e.payload->>'failure_code' IS NULL FOR SHARE OF e;
                IF (refined_observation.seq<natural_finish.seq AND natural_finish.round_index=source_thread.issued_count
                    AND refined_observation.recorded_at<=natural_finish.recorded_at
                    AND natural_finish.recorded_at<=clock_timestamp()) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF EXISTS (SELECT 1 FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL') THEN
                    IF (SELECT count(*) FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL')<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT e.* INTO natural_terminal FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL' FOR SHARE OF e;
                    IF (natural_finish.payload->>'status'='AWAITING_CONTINUE'
                        AND natural_terminal.payload->>'reason'='stop'
                        AND natural_terminal.round_index=source_thread.issued_count
                        AND natural_terminal.operation_id IS NULL AND natural_terminal.attempt_id IS NULL
                        AND natural_finish.seq<natural_terminal.seq
                        AND natural_terminal.seq=(SELECT max(e.seq) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id AND e.seq<mixed_first_correction.seq)
                        AND natural_finish.recorded_at<=natural_terminal.recorded_at
                        AND natural_terminal.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                ELSE
                    IF source_thread.data->>'natural_question_stop' IS NOT NULL
                       OR EXISTS (SELECT 1 FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL')
                       OR natural_finish.payload->>'status' IS DISTINCT FROM 'COMPLETED'
                       OR natural_finish.seq IS DISTINCT FROM
                            (SELECT max(e.seq) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id AND e.seq<mixed_first_correction.seq) THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END IF;
                -- Prior rounds establish eligibility, not extra Piece sources.
                effective_round_sources := coalesce(true,false);
                effective_has_prior_update := false;
                effective_accepted := '[]'::jsonb;
                effective_inactive := '[]'::jsonb;
                effective_claim_sources := '{}'::jsonb;
                effective_claim_anchors := '{}'::jsonb;
                effective_claim_times := '{}'::jsonb;
                IF source_thread.issued_count>0 THEN
                  IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                    AND e.kind='OPERATION' AND e.payload->>'status'='CONTINUED')<>source_thread.issued_count-1 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                  END IF;
                  chain_previous_finish := natural_initial_finish;
                  FOR chain_round IN 1..source_thread.issued_count LOOP
                    FOREACH chain_kind IN ARRAY ARRAY['QUESTION','ANSWER','MEANING_UPDATE','OBSERVATION'] LOOP
                      IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                          AND e.kind=chain_kind AND e.round_index=chain_round
                          AND (chain_kind<>'OBSERVATION' OR e.payload->>'stage'='REFINED'))<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                      END IF;
                    END LOOP;
                    SELECT e.* INTO chain_question FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='QUESTION' AND e.round_index=chain_round FOR SHARE OF e;
                    SELECT e.* INTO chain_answer FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='ANSWER' AND e.round_index=chain_round FOR SHARE OF e;
                    SELECT e.* INTO chain_checkpoint FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='MEANING_UPDATE' AND e.round_index=chain_round FOR SHARE OF e;
                    SELECT e.* INTO chain_observation FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='OBSERVATION' AND e.round_index=chain_round AND e.payload->>'stage'='REFINED' FOR SHARE OF e;
                    chain_payload := chain_answer.payload->'source';
                IF (jsonb_typeof(chain_payload)='object'
                    AND chain_payload ?& ARRAY['answer_id','thread_id','question_id','round_index',
                        'original_source_ref','answer_text_private','recorded_at','authored_at',
                        'source_version','source_role']
                    AND chain_payload-ARRAY['answer_id','thread_id','question_id','round_index',
                        'original_source_ref','answer_text_private','recorded_at','authored_at',
                        'source_version','source_role']='{}'::jsonb
                    AND chain_payload=correction_expected->'answer_sources'->(chain_round-1)
                    AND chain_answer.kind='ANSWER' AND chain_answer.round_index=chain_round
                    AND chain_payload->>'answer_id'=chain_answer.id::text
                    AND chain_payload->>'thread_id'=source_thread.id::text
                    AND chain_payload->'round_index'=to_jsonb(chain_round)
                    AND chain_payload->>'source_role'='SUPPLEMENTAL_ANSWER'
                    AND chain_payload->>'source_version'='cocolon.cmee.supplemental_answer.v1'
                    AND chain_payload->>'source_version'=
                        r.source_lineage#>>'{observation,supplemental_answer_version}'
                    AND chain_payload->>'original_source_ref'=source_thread.data->>'original_source_ref'
                    AND jsonb_typeof(chain_payload->'answer_text_private')='string'
                    AND length(btrim(chain_payload->>'answer_text_private'))>0
                    AND jsonb_typeof(chain_payload->'recorded_at')='string'
                    AND jsonb_typeof(chain_payload->'authored_at') IN ('string','null')
                    AND chain_question.kind='QUESTION' AND chain_question.round_index=chain_round
                    AND chain_question.question_id=chain_answer.question_id
                    AND chain_payload->>'question_id'=chain_question.question_id
                    AND chain_question.payload->>'question_id'=chain_question.question_id
                    AND chain_question.payload->>'thread_id'=source_thread.id::text
                    AND chain_question.payload->>'schema_version'='cocolon.cmee.emlis_clarification.v1'
                    AND chain_question.payload#>>'{decision,disposition}'='ASK'
                    AND chain_question.payload->>'original_source_ref'=chain_payload->>'original_source_ref'
                    AND chain_question.seq<chain_answer.seq
                    AND chain_answer.seq<chain_checkpoint.seq
                    AND chain_checkpoint.seq<chain_observation.seq
                    AND chain_checkpoint.kind='MEANING_UPDATE'
                    AND chain_checkpoint.payload->>'semantic_schema_version'='cocolon.cmee.emlis_answer_meaning.v1'
                    AND chain_checkpoint.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref'
                    AND chain_checkpoint.payload->>'assessment_status'='RESOLVED'
                    AND chain_checkpoint.payload->'unresolved_parts'='[]'::jsonb
                    AND chain_observation.kind='OBSERVATION' AND chain_observation.round_index=chain_round
                    AND chain_observation.payload->>'stage'='REFINED'
                    AND chain_observation.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref'
                    AND NOT (chain_observation.payload ? 'meaning_checkpoint_ref')
                    AND chain_answer.operation_id=chain_observation.operation_id
                    AND chain_answer.attempt_id=chain_observation.attempt_id
                    AND chain_checkpoint.operation_id=chain_observation.operation_id
                    AND chain_checkpoint.attempt_id=chain_observation.attempt_id
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF effective_round_sources THEN
                    IF (jsonb_typeof(chain_checkpoint.payload)='object'
                        AND chain_checkpoint.payload ?& ARRAY['checkpoint_id','source_prefix_ref','base_meaning_ref',
                            'answer_update','assessment_status','accepted_update_refs','inactive_claim_refs',
                            'unresolved_parts','semantic_schema_version']
                        AND chain_checkpoint.payload-ARRAY['checkpoint_id','source_prefix_ref','base_meaning_ref',
                            'answer_update','assessment_status','accepted_update_refs','inactive_claim_refs',
                            'unresolved_parts','semantic_schema_version']='{}'::jsonb
                        AND chain_checkpoint.payload=correction_expected->'answer_checkpoints'->(chain_round-1)
                        AND chain_checkpoint.payload->>'checkpoint_id' ~ '^emlis-checkpoint-[0-9a-f]{64}$'
                        AND chain_checkpoint.payload->>'base_meaning_ref' ~ '^emlis-base-meaning-[0-9a-f]{64}$'
                        AND jsonb_typeof(chain_checkpoint.payload->'accepted_update_refs')='array'
                        AND jsonb_typeof(chain_checkpoint.payload->'inactive_claim_refs')='array'
                        AND chain_checkpoint.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref'
                        AND (chain_round<>source_thread.issued_count
                            OR (chain_checkpoint.id=refined_checkpoint.id
                                AND chain_checkpoint.id=refined_checkpoint.id
                                AND chain_observation.id=mixed_answer_observation.id
                                AND chain_answer.id=source_thread.latest_answer_event_id))
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                END IF;
                chain_update := chain_checkpoint.payload->'answer_update';
                IF (jsonb_typeof(chain_update)='object'
                    AND chain_update->>'disposition'='MATERIAL_UPDATE'
                    AND chain_update->>'question_ref'=chain_question.question_id
                    AND chain_update->'unresolved_parts'='[]'::jsonb
                    AND jsonb_typeof(chain_update->'updates')='array'
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF chain_round=source_thread.issued_count AND (
                    chain_checkpoint.id IS DISTINCT FROM refined_checkpoint.id
                    OR chain_checkpoint.payload IS DISTINCT FROM refined_checkpoint.payload
                ) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF NOT effective_round_sources THEN
                IF chain_round<source_thread.issued_count AND (jsonb_array_length(chain_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(chain_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                )) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                END IF;
                -- Exact compact, lexically sorted metadata JSON of the existing
                -- freeze_supplemental_answer owner. Byte length is UTF-8 length,
                -- not character count; text is not normalized or concatenated
                -- into the saved original. The resulting digest includes every
                -- answer identity/version/time/parent field and the exact body.
                chain_header := '{"answer_id":'||(chain_payload->'answer_id')::text
                    ||',"authored_at":'||(chain_payload->'authored_at')::text
                    ||',"original_source_ref":'||(chain_payload->'original_source_ref')::text
                    ||',"question_id":'||(chain_payload->'question_id')::text
                    ||',"recorded_at":'||(chain_payload->'recorded_at')::text
                    ||',"round_index":'||(chain_payload->'round_index')::text
                    ||',"source_role":'||(chain_payload->'source_role')::text
                    ||',"source_version":'||(chain_payload->'source_version')::text
                    ||',"thread_id":'||(chain_payload->'thread_id')::text||'}';
                chain_frame_hash := encode(sha256(convert_to(
                    E'CMEE_EMLIS_ANSWER_FRAME_UTF8_V1\n'||chain_header
                    ||E'\n@answer_text_private:'||octet_length(chain_payload->>'answer_text_private')::text
                    ||E'\n'||(chain_payload->>'answer_text_private'),'UTF8')),'hex');
                IF chain_round=source_thread.issued_count AND 'sha256:'||chain_frame_hash IS DISTINCT FROM
                    r.source_lineage#>>'{observation,supplemental_answer_bundle_commitment}' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                chain_envelope_ref := 'src-'||substr(encode(sha256(convert_to(
                    '{"label_contract_digest":"","label_contract_id":"","raw_sha256":"'
                    ||chain_frame_hash||'","schema":"cocolon.cmee.source_envelope.identity.v2",'
                    ||'"source_contract_version":"cocolon.cmee.emlis_thread.v1",'
                    ||'"source_encoding":"CMEE_EMLIS_ANSWER_FRAME_UTF8_V1","source_record_id":'
                    ||(chain_payload->'answer_id')::text
                    ||',"source_role":"SUPPLEMENTAL_ANSWER","source_schema_version":"cocolon.cmee.supplemental_answer.v1"}',
                    'UTF8')),'hex'),1,24);
                IF chain_update->>'answer_source_ref' IS DISTINCT FROM chain_envelope_ref THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF effective_round_sources THEN
                    IF (chain_update ?& ARRAY['answer_source_ref','question_ref','prior_meaning_ref','updates',
                            'unresolved_parts','disposition','new_meaning_ref']
                        AND chain_update-ARRAY['answer_source_ref','question_ref','prior_meaning_ref','updates',
                            'unresolved_parts','disposition','new_meaning_ref']='{}'::jsonb
                        AND chain_update->>'prior_meaning_ref'=chain_checkpoint.payload->>'base_meaning_ref'
                        AND chain_update->>'new_meaning_ref' ~ '^emlis-meaning-[0-9a-f]{64}$'
                        AND jsonb_array_length(chain_update->'updates')>=1
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    FOR effective_item IN SELECT value FROM jsonb_array_elements(chain_update->'updates') LOOP
                        IF (jsonb_typeof(effective_item)='object'
                            AND effective_item ?& ARRAY['update_ref','binding_kind','target_meaning_refs','evidence_refs',
                                'temporal_binding','operation','changed_claim_refs','superseded_claim_refs','affected_dependency_refs']
                            AND effective_item-ARRAY['update_ref','binding_kind','target_meaning_refs','evidence_refs',
                                'temporal_binding','operation','changed_claim_refs','superseded_claim_refs','affected_dependency_refs']='{}'::jsonb
                            AND effective_item->>'update_ref' ~ '^emlis-update-[0-9a-f]{64}$'
                            AND NOT (effective_accepted ? (effective_item->>'update_ref'))
                            AND effective_item->>'operation' IN ('ADD','REVISE','WITHDRAW')
                            AND jsonb_typeof(effective_item->'target_meaning_refs')='array'
                            AND jsonb_typeof(effective_item->'evidence_refs')='array'
                            AND jsonb_typeof(effective_item->'changed_claim_refs')='array'
                            AND jsonb_typeof(effective_item->'superseded_claim_refs')='array'
                            AND jsonb_typeof(effective_item->'affected_dependency_refs')='array'
                            AND jsonb_typeof(effective_item->'temporal_binding')='object'
                        ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                        FOREACH effective_ref_kind IN ARRAY ARRAY['target_meaning_refs','evidence_refs',
                            'changed_claim_refs','superseded_claim_refs','affected_dependency_refs'] LOOP
                            IF EXISTS (SELECT 1 FROM jsonb_array_elements(effective_item->effective_ref_kind) ref
                                WHERE jsonb_typeof(ref) IS DISTINCT FROM 'string')
                                OR (SELECT count(*) FROM jsonb_array_elements(effective_item->effective_ref_kind))<>
                                   (SELECT count(DISTINCT value) FROM jsonb_array_elements(effective_item->effective_ref_kind)) THEN
                                RAISE EXCEPTION 'PIECE_CONFLICT';
                            END IF;
                        END LOOP;
                        IF (jsonb_array_length(effective_item->'target_meaning_refs')=1
                            AND ((effective_item->>'operation'='ADD'
                                    AND effective_item->'target_meaning_refs'=jsonb_build_array(
                                        chain_question.payload#>'{decision,affected_meaning_refs,0}'))
                                OR (effective_item->>'operation' IN ('REVISE','WITHDRAW')
                                    AND effective_item#>>'{target_meaning_refs,0}' ~ '^(nucleus|answer):s[0-9]+$'))
                            AND jsonb_array_length(effective_item->'evidence_refs')=1
                            AND effective_item#>>'{evidence_refs,0}' ~ '^ev-[0-9a-f]{24}$'
                            AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements_text(effective_item->'changed_claim_refs') ref
                                WHERE ref !~ '^answer:s[0-9]+$' OR effective_claim_sources ? ref
                                    OR effective_inactive ? ref)
                            AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements_text(effective_item->'affected_dependency_refs') ref
                                WHERE ref !~ '^relation:r[0-9]+$')
                        ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                        effective_temporal := effective_item->'temporal_binding';
                        IF (effective_temporal ?& ARRAY['about_time','anchor_source_ref','time_expression_evidence_refs',
                                'relative_relation','resolved_interval','timezone_basis']
                            AND effective_temporal-ARRAY['about_time','anchor_source_ref','time_expression_evidence_refs',
                                'relative_relation','resolved_interval','timezone_basis']='{}'::jsonb
                            AND effective_temporal->>'about_time' IN ('ORIGINAL_OCCASION','ANSWER_TIME')
                            AND jsonb_typeof(effective_temporal->'anchor_source_ref')='string'
                            AND effective_temporal->'resolved_interval'='null'::jsonb
                            AND effective_temporal->'timezone_basis'='null'::jsonb
                            AND (effective_temporal->'time_expression_evidence_refs'='[]'::jsonb
                                OR effective_temporal->'time_expression_evidence_refs'=effective_item->'evidence_refs')
                        ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                        effective_target := effective_item#>>'{target_meaning_refs,0}';
                        IF effective_item->>'operation'='ADD' THEN
                            IF (effective_item->>'binding_kind' IN ('QUESTION_FOCUS','SAME_OCCASION_CURRENT_STATE')
                                AND effective_item->'superseded_claim_refs'='[]'::jsonb
                                AND effective_item->'affected_dependency_refs'='[]'::jsonb
                                AND jsonb_array_length(effective_item->'changed_claim_refs')=1
                                AND effective_temporal->>'anchor_source_ref'=source_thread.data->>'original_source_ref'
                                AND ((effective_temporal->>'about_time'='ORIGINAL_OCCASION'
                                        AND effective_temporal->'relative_relation'='null'::jsonb)
                                    OR (effective_temporal->>'about_time'='ANSWER_TIME'
                                        AND effective_temporal->>'relative_relation'='answer_deictic_now'
                                        AND effective_temporal->'time_expression_evidence_refs'=effective_item->'evidence_refs'))
                            ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                            effective_anchor := CASE WHEN effective_temporal->>'about_time'='ANSWER_TIME'
                                THEN chain_envelope_ref ELSE source_thread.data->>'original_source_ref' END;
                        ELSE
                            IF (jsonb_array_length(chain_update->'updates')=1
                                AND effective_item->>'binding_kind'='EXPLICIT_CORRECTION'
                                AND effective_item->'superseded_claim_refs'=effective_item->'target_meaning_refs'
                                AND NOT (effective_inactive ? effective_target)
                                AND ((effective_item->>'operation'='REVISE'
                                        AND jsonb_array_length(effective_item->'changed_claim_refs')=1)
                                    OR (effective_item->>'operation'='WITHDRAW'
                                        AND effective_item->'changed_claim_refs'='[]'::jsonb))
                                AND effective_temporal->'time_expression_evidence_refs'='[]'::jsonb
                            ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                            IF effective_target ~ '^answer:' THEN
                                IF (effective_claim_sources ? effective_target
                                    AND effective_claim_sources->>effective_target<>chain_envelope_ref
                                    AND effective_temporal->>'about_time'=effective_claim_times->>effective_target
                                    AND effective_temporal->>'anchor_source_ref'=effective_claim_anchors->>effective_target
                                    AND ((effective_temporal->>'about_time'='ORIGINAL_OCCASION'
                                            AND effective_temporal->'relative_relation'='null'::jsonb)
                                        OR (effective_temporal->>'about_time'='ANSWER_TIME'
                                            AND effective_temporal->>'relative_relation'='revision_of_answer_time'))
                                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                            ELSE
                                IF (effective_temporal->>'about_time'='ORIGINAL_OCCASION'
                                    AND effective_temporal->>'anchor_source_ref'=source_thread.data->>'original_source_ref'
                                    AND effective_temporal->'relative_relation'='null'::jsonb
                                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                            END IF;
                            effective_anchor := effective_temporal->>'anchor_source_ref';
                            IF chain_round<source_thread.issued_count OR effective_target ~ '^answer:' THEN
                                effective_has_prior_update := true;
                            END IF;
                        END IF;
                        -- ADD may point at question focus, but an ANSWER focus
                        -- still has to have existed and remain active here.
                        IF effective_target ~ '^answer:' AND (NOT (effective_claim_sources ? effective_target)
                            OR effective_inactive ? effective_target) THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                        effective_accepted := effective_accepted||jsonb_build_array(effective_item->>'update_ref');
                        FOR effective_ref IN SELECT value FROM jsonb_array_elements_text(
                            (effective_item->'superseded_claim_refs')||(effective_item->'affected_dependency_refs')) LOOP
                            IF NOT (effective_inactive ? effective_ref) THEN
                                effective_inactive := effective_inactive||jsonb_build_array(effective_ref);
                            END IF;
                        END LOOP;
                        FOR effective_ref IN SELECT value FROM jsonb_array_elements_text(effective_item->'changed_claim_refs') LOOP
                            effective_claim_sources := effective_claim_sources||jsonb_build_object(effective_ref,chain_envelope_ref);
                            effective_claim_anchors := effective_claim_anchors||jsonb_build_object(effective_ref,effective_anchor);
                            effective_claim_times := effective_claim_times||jsonb_build_object(effective_ref,effective_temporal->>'about_time');
                        END LOOP;
                    END LOOP;
                    IF chain_checkpoint.payload->'accepted_update_refs' IS DISTINCT FROM effective_accepted
                        OR chain_checkpoint.payload->'inactive_claim_refs' IS DISTINCT FROM effective_inactive THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END IF;
                    IF (chain_checkpoint.round_index=chain_round
                        AND jsonb_typeof(chain_checkpoint.payload->'checkpoint_id')='string'
                        AND length(chain_checkpoint.payload->>'checkpoint_id')>0
                        AND chain_question.recorded_at<=(chain_payload->>'recorded_at')::timestamptz
                        AND (chain_round>1 OR natural_initial_finish.recorded_at<=(chain_payload->>'recorded_at')::timestamptz)
                        AND (chain_payload->>'recorded_at')::timestamptz<=chain_answer.recorded_at
                        AND chain_question.recorded_at<=chain_answer.recorded_at
                        AND chain_answer.recorded_at<=chain_checkpoint.recorded_at
                        AND chain_checkpoint.recorded_at<=chain_observation.recorded_at
                        AND chain_observation.recorded_at<=clock_timestamp()
                        AND chain_observation.payload->>'context_ref'=natural_context_ref
                        AND coalesce(chain_observation.payload->'context_guards','[]'::jsonb)=natural_guards
                        AND jsonb_typeof(chain_observation.payload->'source_prefix_ref')='string'
                        AND length(chain_observation.payload->>'source_prefix_ref')>0
                        AND chain_observation.payload->>'source_prefix_ref' !~ '[[:space:]]'
                        AND jsonb_typeof(chain_observation.payload->'text')='string'
                        AND length(btrim(chain_observation.payload->>'text'))>0
                        AND chain_observation.payload#>>'{artifact,schema_version}'='cocolon.emlis.recipient_reply.v1'
                        AND public.piece_natural_analysis_artifact_valid(
                            chain_observation.payload->'artifact',chain_observation.payload->>'source_prefix_ref',
                            source_thread.user_id,source_thread.source_snapshot)
                        AND jsonb_typeof(chain_observation.payload#>'{artifact,model}')='string'
                        AND length(btrim(chain_observation.payload#>>'{artifact,model}'))>0
                        AND chain_observation.payload#>'{artifact,text}'=chain_observation.payload->'text'
                        AND chain_observation.operation_id IS NOT NULL AND chain_observation.attempt_id IS NOT NULL
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    FOREACH chain_stage IN ARRAY ARRAY['NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'] LOOP
                      IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                          AND e.kind='OPERATION' AND e.payload->>'stage'=chain_stage
                          AND e.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref')<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                      END IF;
                    END LOOP;
                    SELECT e.* INTO chain_started FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='OPERATION' AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED'
                      AND e.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref' FOR SHARE OF e;
                    SELECT e.* INTO chain_received FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='OPERATION' AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED'
                      AND e.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref' FOR SHARE OF e;
                    IF (chain_started.round_index=chain_round AND chain_received.round_index=chain_round
                        AND chain_started.operation_id=chain_observation.operation_id AND chain_received.operation_id=chain_observation.operation_id
                        AND chain_started.attempt_id=chain_observation.attempt_id AND chain_received.attempt_id=chain_observation.attempt_id
                        AND chain_started.payload->>'context_ref'=natural_context_ref AND chain_received.payload->>'context_ref'=natural_context_ref
                        AND chain_started.payload->>'response_stage'='REFINED' AND chain_received.payload->>'response_stage'='REFINED'
                        AND chain_received.payload->'reply'=jsonb_build_object('text',chain_observation.payload->'text',
                          'model',chain_observation.payload#>'{artifact,model}',
                          'source_prefix_ref',chain_observation.payload->>'source_prefix_ref',
                          'schema_version','cocolon.emlis.recipient_reply.v1')
                        AND chain_checkpoint.seq<chain_started.seq AND chain_started.seq<chain_received.seq
                        AND chain_received.seq<chain_observation.seq
                        AND chain_checkpoint.recorded_at<=chain_started.recorded_at
                        AND chain_started.recorded_at<=chain_received.recorded_at
                        AND chain_received.recorded_at<=chain_observation.recorded_at
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF chain_round>1 THEN
                      IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                          AND e.kind='OPERATION' AND e.payload->>'status'='CONTINUED' AND e.round_index=chain_round)<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                      END IF;
                      SELECT e.* INTO chain_continued FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.payload->>'status'='CONTINUED' AND e.round_index=chain_round FOR SHARE OF e;
                      IF (chain_previous_finish.payload->>'status'='AWAITING_CONTINUE'
                          AND chain_previous_finish.seq<chain_question.seq AND chain_question.seq<chain_continued.seq
                          AND chain_continued.seq<chain_answer.seq AND chain_question.operation_id IS NULL
                          AND chain_question.attempt_id IS NULL AND chain_continued.operation_id IS NULL
                          AND chain_continued.attempt_id IS NULL
                          AND chain_previous_finish.recorded_at<=chain_question.recorded_at
                          AND chain_question.recorded_at<=chain_continued.recorded_at
                          AND chain_continued.recorded_at<=chain_answer.recorded_at
                          AND chain_continued.recorded_at<=(chain_payload->>'recorded_at')::timestamptz
                      ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    END IF;
                    IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=chain_observation.operation_id
                        AND e.attempt_id=chain_observation.attempt_id AND e.payload->>'status' IN ('COMPLETED','AWAITING_CONTINUE')
                        AND e.payload->>'failure_code' IS NULL)<>1 THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    SELECT e.* INTO chain_finish FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                      AND e.kind='OPERATION' AND e.operation_id=chain_observation.operation_id
                      AND e.attempt_id=chain_observation.attempt_id AND e.payload->>'status' IN ('COMPLETED','AWAITING_CONTINUE')
                      AND e.payload->>'failure_code' IS NULL FOR SHARE OF e;
                    IF (chain_finish.round_index=chain_round AND chain_observation.seq<chain_finish.seq
                        AND chain_observation.recorded_at<=chain_finish.recorded_at AND chain_finish.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    chain_previous_finish := chain_finish;
                  END LOOP;
                END IF;
                IF natural_finish.seq>=mixed_first_correction.seq
                    OR natural_finish.recorded_at>(mixed_first_correction.payload#>>'{source,recorded_at}')::timestamptz
                    OR (natural_terminal.id IS NOT NULL AND natural_terminal.recorded_at>(mixed_first_correction.payload#>>'{source,recorded_at}')::timestamptz)
                    OR EXISTS (SELECT 1 FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind IN ('QUESTION','ANSWER','MEANING_UPDATE','TERMINAL')
                        AND e.seq>=mixed_first_correction.seq) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.id,e.payload->>'source_prefix_ref' INTO correction_previous_id,correction_base_prefix
                    FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                    AND e.id=mixed_answer_observation.id;
                IF correction_previous_id IS NULL OR correction_base_prefix !~ '^emlis-q3-source-prefix-[0-9a-f]{64}$' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_previous_prefix := correction_base_prefix;
                correction_headers := '';
                FOR correction_source, correction_step IN SELECT value,ordinality::integer
                    FROM jsonb_array_elements(correction_history) WITH ORDINALITY LOOP
                IF (jsonb_typeof(correction_expected)='object'
                    AND correction_expected ?& ARRAY['source','source_prefix_ref','events','thread_data']
                    AND correction_expected-ARRAY['source','source_prefix_ref','events','thread_data','prior_sources','answer_sources','answer_checkpoints']='{}'::jsonb
                    AND jsonb_typeof(correction_source)='object'
                    AND correction_source ?& ARRAY['correction_id','thread_id','original_source_ref',
                        'target_event_id','target_text','explanation','recorded_at','source_role']
                    AND correction_source-ARRAY['correction_id','thread_id','original_source_ref',
                        'target_event_id','target_text','explanation','recorded_at','source_role']='{}'::jsonb
                    AND correction_source->>'source_role'='USER_INTERPRETATION_CORRECTION'
                    AND correction_source->>'thread_id'=source_thread.id::text
                    AND correction_source->>'original_source_ref'=source_thread.data->>'original_source_ref'
                    AND correction_source->>'correction_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    AND correction_source->>'target_event_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    AND jsonb_typeof(correction_source->'explanation')='string'
                    AND length(btrim(correction_source->>'explanation')) BETWEEN 1 AND 2000
                    AND jsonb_typeof(correction_source->'target_text')='string'
                    AND length(btrim(correction_source->>'target_text')) BETWEEN 1 AND 2000
                    AND jsonb_typeof(correction_source->'recorded_at')='string'
                    AND jsonb_typeof(correction_expected->'events')='array'
                    AND correction_expected->'thread_data'=source_thread.data
                    AND correction_expected->>'source_prefix_ref'=source_thread.source_prefix_ref
                    AND source_thread.source_prefix_ref ~ '^emlis-corrected-source-prefix-[0-9a-f]{64}$'
                    AND source_thread.data->>'runtime_profile'='q3.plan.sequential.v1'
                    AND source_thread.data->>'response_profile'='natural_reply.v1'
                    AND source_thread.state='COMPLETED' AND source_thread.issued_count IN (1,2,3)
                    AND source_thread.latest_answer_event_id IS NOT NULL
                    AND source_thread.current_meaning_event_id IS NULL
                    AND source_thread.evaluated_prefix_ref IS NULL
                    AND source_thread.active_operation_id IS NULL
                    AND source_thread.active_attempt_id IS NULL
                    AND source_thread.processing_deadline_at IS NULL
                    AND source_thread.data->>'body_state'='FINAL'
                    AND source_thread.data->>'natural_response_stage'='FINAL'
                    AND source_thread.data->>'answer_assessment'='RESOLVED'
                    AND source_thread.data->>'failure_code' IS NULL
                    AND source_thread.data->>'semantic_profile' IS NULL
                    AND (source_thread.data->'meaning_updated' IS NULL
                        OR source_thread.data->'meaning_updated' IN ('null'::jsonb,'false'::jsonb))
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                PERFORM 1 FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id ORDER BY e.seq FOR SHARE OF e;
                SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.seq),'[]'::jsonb)
                    INTO correction_events FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id;
                IF correction_events IS DISTINCT FROM correction_expected->'events'
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OBSERVATION')<>source_thread.issued_count+correction_count+1
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.payload->>'stage'='INTERPRETATION_CORRECTION')<>correction_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO correction_event FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage'='INTERPRETATION_CORRECTION'
                      AND e.id::text=correction_source->>'correction_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_target FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.id::text=correction_source->>'target_event_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_body FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION'
                      AND e.operation_id=correction_event.operation_id AND e.attempt_id=correction_event.attempt_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (correction_event.id::text=correction_source->>'correction_id'
                    AND correction_event.round_index=source_thread.issued_count AND correction_event.question_id IS NULL
                    AND correction_event.payload->'source'=correction_source
                    AND correction_event.payload->>'status'='SAVED'
                    AND correction_event.payload->>'assessment'='UNASSESSED'
                    AND correction_event.idempotency_key IS NOT NULL
                    AND correction_event.operation_id IS NOT NULL AND correction_event.attempt_id IS NOT NULL
                    AND correction_target.kind='OBSERVATION' AND correction_target.round_index=source_thread.issued_count
                    AND correction_target.id=correction_previous_id
                    AND correction_target.payload->>'stage'=CASE WHEN correction_step=1 THEN 'REFINED' ELSE 'CORRECTED' END
                    AND correction_target.payload->>'source_prefix_ref'=correction_previous_prefix
                    AND correction_target.payload->>'source_prefix_ref'<>source_thread.source_prefix_ref
                    AND correction_body.kind='OBSERVATION' AND correction_body.round_index=source_thread.issued_count
                    AND correction_body.payload->>'stage'='CORRECTED'
                    AND (correction_step<>correction_count OR (correction_body.id=source_thread.last_observation_event_id
                        AND correction_body.payload->>'source_prefix_ref'=source_thread.source_prefix_ref))
                    AND correction_body.operation_id=correction_event.operation_id
                    AND correction_body.attempt_id=correction_event.attempt_id
                    AND (correction_step<>correction_count OR (
                        correction_body.operation_id::text=source_thread.data->>'operation_id'
                        AND correction_body.attempt_id::text=source_thread.data->>'attempt_id'))
                    AND correction_target.seq<correction_event.seq AND correction_event.seq<correction_body.seq
                    AND correction_target.recorded_at<=(correction_source->>'recorded_at')::timestamptz
                    AND correction_target.recorded_at<=correction_event.recorded_at
                    AND (correction_source->>'recorded_at')::timestamptz<=correction_event.recorded_at
                    AND correction_event.recorded_at<=correction_body.recorded_at
                    AND correction_body.recorded_at<=clock_timestamp()
                    AND NOT (correction_target.payload ? 'meaning_checkpoint_ref')
                    AND NOT (correction_body.payload ? 'meaning_checkpoint_ref')
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                correction_excerpt := correction_source->>'target_text';
                correction_target_text := correction_target.payload->>'text';
                correction_excerpt_at := strpos(correction_target_text,correction_excerpt);
                IF correction_excerpt_at<1 OR strpos(substr(correction_target_text,
                    correction_excerpt_at+1),correction_excerpt)>0 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                -- Exact compact metadata, with no normalization of either
                -- explanation or quoted AI locator. The separate raw frame
                -- contains only the person's explanation as evidence text.
                correction_header := '{"correction_id":'||(correction_source->'correction_id')::text
                    ||',"explanation":'||(correction_source->'explanation')::text
                    ||',"original_source_ref":'||(correction_source->'original_source_ref')::text
                    ||',"recorded_at":'||(correction_source->'recorded_at')::text
                    ||',"source_role":'||(correction_source->'source_role')::text
                    ||',"target_event_id":'||(correction_source->'target_event_id')::text
                    ||',"target_text":'||(correction_source->'target_text')::text
                    ||',"thread_id":'||(correction_source->'thread_id')::text||'}';
                -- Each historical prefix is BASE + the full ordered history
                -- through this source, never a recursive corrected-prefix hash.
                correction_headers := correction_headers || CASE WHEN correction_step=1 THEN '' ELSE ',' END || correction_header;
                correction_prefix := 'emlis-corrected-source-prefix-'||encode(sha256(convert_to(
                    '['||to_jsonb(correction_base_prefix)::text||',['||correction_headers||']]','UTF8')),'hex');
                IF correction_body.payload->>'source_prefix_ref' IS DISTINCT FROM correction_prefix
                    OR (correction_step=correction_count AND source_thread.source_prefix_ref IS DISTINCT FROM correction_prefix) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_frame := 'memo:'||octet_length(convert_to(correction_source->>'explanation','UTF8'))::text
                    ||':'||(correction_source->>'explanation')||'memo_action:0:';
                IF correction_step=correction_count AND (r.source_lineage#>>'{interpretation_correction_source,correction_id}'=correction_event.id::text
                    AND r.source_lineage#>>'{interpretation_correction_source,target_event_id}'=correction_target.id::text
                    AND r.source_lineage#>>'{interpretation_correction_source,source_version}'=
                        'sha256:'||encode(sha256(convert_to(correction_header,'UTF8')),'hex')
                    AND r.source_lineage#>>'{interpretation_correction_source,explanation_commitment}'=
                        'sha256:'||encode(sha256(convert_to(correction_frame,'UTF8')),'hex')
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                -- Exact compact array serialization of the existing identity(
                -- 'context', tier, guards, feedback); only typed scalar arrays
                -- enter this digest, so no whitespace is removed from strings.
                natural_guards := coalesce(source_thread.data->'context_guards','[]'::jsonb);
                natural_feedback := coalesce(source_thread.data->'context_feedback','[]'::jsonb);
                IF jsonb_typeof(natural_guards) IS DISTINCT FROM 'array'
                   OR jsonb_typeof(natural_feedback) IS DISTINCT FROM 'array' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF EXISTS (SELECT 1 FROM jsonb_array_elements(natural_guards) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>3
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->2) IS DISTINCT FROM 'number'
                          OR (x.value->>2) !~ '^(0|[1-9][0-9]*)$' END)
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(natural_feedback) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>2
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'number'
                          OR (x.value->>1) !~ '^(0|[1-9][0-9]*)$' END) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||','||(x.value->2)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_guard_header
                    FROM jsonb_array_elements(natural_guards) WITH ORDINALITY x(value,ordinality);
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_feedback_header
                    FROM jsonb_array_elements(natural_feedback) WITH ORDINALITY x(value,ordinality);
                natural_context_ref := 'context-'||encode(sha256(convert_to(
                    '['||to_jsonb(tier)::text||','||natural_guard_header||','||natural_feedback_header||']',
                    'UTF8')),'hex');
                IF jsonb_array_length(coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb))>0 THEN
                    SELECT '['||coalesce(string_agg(to_jsonb(
                        (x.value->>0)||':'||(x.value->>1)||':'||(x.value->>2)||':'||
                        (x.value->>3)||':'||(x.value->>4)||':'||(x.value->>5))::text,
                        ',' ORDER BY x.ordinality),'')||']' INTO natural_target_tokens
                        FROM jsonb_array_elements(source_thread.data->'frame_target_dependencies') WITH ORDINALITY x(value,ordinality);
                    natural_context_ref := 'context-frame-targets-'||encode(sha256(convert_to(
                        '['||to_jsonb(natural_context_ref)::text||','||natural_target_tokens||']','UTF8')),'hex');
                END IF;
                -- Same receipt and completion checks as the natural arm,
                -- with FINAL response_stage and no fictitious question/checkpoint.
                FOR natural_body IN SELECT e.* FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id
                      AND e.id IN (correction_target.id,correction_body.id) ORDER BY e.seq LOOP
                    IF correction_step=1 AND natural_body.id=mixed_answer_observation.id THEN
                        CONTINUE; -- Its complete answer prefix was validated above.
                    END IF;
                    natural_prefix := natural_body.payload->>'source_prefix_ref';
                    IF (natural_body.operation_id IS NOT NULL AND natural_body.attempt_id IS NOT NULL
                        AND natural_body.question_id IS NULL
                        AND natural_body.payload->>'context_ref'=natural_context_ref
                        AND natural_body.payload->'context_guards'=natural_guards
                        AND jsonb_typeof(natural_body.payload->'text')='string'
                        AND length(btrim(natural_body.payload->>'text'))>0
                        AND natural_body.payload#>>'{artifact,schema_version}'='cocolon.emlis.recipient_reply.v1'
                        AND natural_body.payload#>'{artifact,text}'=natural_body.payload->'text'
                        AND jsonb_typeof(natural_body.payload#>'{artifact,model}')='string'
                        AND length(btrim(natural_body.payload#>>'{artifact,model}'))>0
                        AND public.piece_natural_analysis_artifact_valid(natural_body.payload->'artifact',
                            natural_prefix,source_thread.user_id,source_thread.source_snapshot)
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED')<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED')<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'status'='COMPLETED'
                        AND e.payload->>'failure_code' IS NULL)<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT e.* INTO natural_started FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED';
                    SELECT e.* INTO natural_received FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED';
                    SELECT e.* INTO correction_finish FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'status'='COMPLETED' AND e.payload->>'failure_code' IS NULL;
                    IF (natural_started.round_index=source_thread.issued_count AND natural_received.round_index=source_thread.issued_count
                        AND correction_finish.round_index=source_thread.issued_count AND natural_body.round_index=source_thread.issued_count
                        AND natural_started.payload->>'source_prefix_ref'=natural_prefix
                        AND natural_received.payload->>'source_prefix_ref'=natural_prefix
                        AND natural_started.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_received.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_started.payload->>'response_stage'='FINAL'
                        AND natural_received.payload->>'response_stage'='FINAL'
                        AND natural_received.payload->'reply'=jsonb_build_object('text',natural_body.payload->'text',
                            'model',natural_body.payload#>'{artifact,model}','source_prefix_ref',natural_prefix,
                            'schema_version','cocolon.emlis.recipient_reply.v1')
                        AND natural_started.seq<natural_received.seq AND natural_received.seq<natural_body.seq
                        AND natural_body.seq<correction_finish.seq
                        AND source_created AT TIME ZONE 'UTC'<=natural_started.recorded_at
                        AND natural_started.recorded_at<=natural_received.recorded_at
                        AND natural_received.recorded_at<=natural_body.recorded_at
                        AND natural_body.recorded_at<=correction_finish.recorded_at
                        AND correction_finish.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF natural_body.id=correction_target.id THEN
                        IF correction_finish.seq>=correction_event.seq
                           OR correction_finish.recorded_at>(correction_source->>'recorded_at')::timestamptz THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                    ELSIF correction_event.seq>=natural_started.seq
                       OR correction_event.recorded_at>natural_started.recorded_at THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END LOOP;
                correction_previous_id := correction_body.id;
                correction_previous_prefix := correction_prefix;
                END LOOP;
                ELSE
                IF (r.source_lineage->'semantic_source_roles'='["original_input","interpretation_correction"]'::jsonb
                    AND r.source_lineage->'lineage_control_roles'='["emlis_observation_result","ai_interpretation_target"]'::jsonb
                    AND r.source_lineage#>'{observation,question_need_decision_identity}'='null'::jsonb
                    AND r.source_lineage#>'{observation,supplemental_answer_identity}'='null'::jsonb
                    AND r.source_lineage#>'{observation,supplemental_answer_version}'='null'::jsonb
                    AND r.source_lineage#>'{observation,supplemental_answer_bundle_commitment}'='null'::jsonb) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                -- A real two-input correction is neither an ANSWER nor an
                -- INITIAL-only source. Lock the exact accepted source prefix.
                correction_expected := p_expected_source_state->'interpretation_correction';
                IF (jsonb_typeof(correction_expected)='object'
                    AND (NOT (correction_expected ? 'prior_sources')
                        OR (jsonb_typeof(correction_expected->'prior_sources')='array'
                            AND CASE WHEN jsonb_typeof(correction_expected->'prior_sources')='array' THEN jsonb_array_length(correction_expected->'prior_sources')>0 ELSE false END))) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_history := coalesce(correction_expected->'prior_sources','[]'::jsonb)
                    || jsonb_build_array(correction_expected->'source');
                correction_count := jsonb_array_length(correction_history);
                IF correction_count<1 OR (SELECT count(DISTINCT x.value->>'correction_id')
                    FROM jsonb_array_elements(correction_history) x(value))<>correction_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.id,e.payload->>'source_prefix_ref' INTO correction_previous_id,correction_base_prefix
                    FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                    AND e.kind='OBSERVATION' ORDER BY e.seq LIMIT 1;
                IF correction_previous_id IS NULL OR correction_base_prefix !~ '^emlis-q3-source-prefix-[0-9a-f]{64}$' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_previous_prefix := correction_base_prefix;
                correction_headers := '';
                FOR correction_source, correction_step IN SELECT value,ordinality::integer
                    FROM jsonb_array_elements(correction_history) WITH ORDINALITY LOOP
                IF (jsonb_typeof(correction_expected)='object'
                    AND correction_expected ?& ARRAY['source','source_prefix_ref','events','thread_data']
                    AND correction_expected-ARRAY['source','source_prefix_ref','events','thread_data','prior_sources']='{}'::jsonb
                    AND jsonb_typeof(correction_source)='object'
                    AND correction_source ?& ARRAY['correction_id','thread_id','original_source_ref',
                        'target_event_id','target_text','explanation','recorded_at','source_role']
                    AND correction_source-ARRAY['correction_id','thread_id','original_source_ref',
                        'target_event_id','target_text','explanation','recorded_at','source_role']='{}'::jsonb
                    AND correction_source->>'source_role'='USER_INTERPRETATION_CORRECTION'
                    AND correction_source->>'thread_id'=source_thread.id::text
                    AND correction_source->>'original_source_ref'=source_thread.data->>'original_source_ref'
                    AND correction_source->>'correction_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    AND correction_source->>'target_event_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    AND jsonb_typeof(correction_source->'explanation')='string'
                    AND length(btrim(correction_source->>'explanation')) BETWEEN 1 AND 2000
                    AND jsonb_typeof(correction_source->'target_text')='string'
                    AND length(btrim(correction_source->>'target_text')) BETWEEN 1 AND 2000
                    AND jsonb_typeof(correction_source->'recorded_at')='string'
                    AND jsonb_typeof(correction_expected->'events')='array'
                    AND correction_expected->'thread_data'=source_thread.data
                    AND correction_expected->>'source_prefix_ref'=source_thread.source_prefix_ref
                    AND source_thread.source_prefix_ref ~ '^emlis-corrected-source-prefix-[0-9a-f]{64}$'
                    AND source_thread.data->>'runtime_profile'='q3.plan.sequential.v1'
                    AND source_thread.data->>'response_profile'='natural_reply.v1'
                    AND source_thread.state='COMPLETED' AND source_thread.issued_count=0
                    AND source_thread.latest_answer_event_id IS NULL
                    AND source_thread.current_meaning_event_id IS NULL
                    AND source_thread.evaluated_prefix_ref IS NULL
                    AND source_thread.active_operation_id IS NULL
                    AND source_thread.active_attempt_id IS NULL
                    AND source_thread.processing_deadline_at IS NULL
                    AND source_thread.data->>'body_state'='FINAL'
                    AND source_thread.data->>'natural_response_stage'='FINAL'
                    AND source_thread.data->>'answer_assessment'='NOT_APPLICABLE'
                    AND source_thread.data->>'failure_code' IS NULL
                    AND source_thread.data->>'semantic_profile' IS NULL
                    AND (source_thread.data->'meaning_updated' IS NULL
                        OR source_thread.data->'meaning_updated' IN ('null'::jsonb,'false'::jsonb))
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                PERFORM 1 FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id ORDER BY e.seq FOR SHARE OF e;
                SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.seq),'[]'::jsonb)
                    INTO correction_events FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id;
                IF correction_events IS DISTINCT FROM correction_expected->'events'
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind IN ('QUESTION','ANSWER','MEANING_UPDATE','TERMINAL'))<>0
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OBSERVATION')<>correction_count+1
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.payload->>'stage'='INTERPRETATION_CORRECTION')<>correction_count THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO correction_event FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage'='INTERPRETATION_CORRECTION'
                      AND e.id::text=correction_source->>'correction_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_target FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.id::text=correction_source->>'target_event_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_body FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION'
                      AND e.operation_id=correction_event.operation_id AND e.attempt_id=correction_event.attempt_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (correction_event.id::text=correction_source->>'correction_id'
                    AND correction_event.round_index=0 AND correction_event.question_id IS NULL
                    AND correction_event.payload->'source'=correction_source
                    AND correction_event.payload->>'status'='SAVED'
                    AND correction_event.payload->>'assessment'='UNASSESSED'
                    AND correction_event.idempotency_key IS NOT NULL
                    AND correction_event.operation_id IS NOT NULL AND correction_event.attempt_id IS NOT NULL
                    AND correction_target.kind='OBSERVATION' AND correction_target.round_index=0
                    AND correction_target.id=correction_previous_id
                    AND correction_target.payload->>'stage'=CASE WHEN correction_step=1 THEN 'INITIAL' ELSE 'CORRECTED' END
                    AND correction_target.payload->>'source_prefix_ref'=correction_previous_prefix
                    AND correction_target.payload->>'source_prefix_ref'<>source_thread.source_prefix_ref
                    AND correction_body.kind='OBSERVATION' AND correction_body.round_index=0
                    AND correction_body.payload->>'stage'='CORRECTED'
                    AND (correction_step<>correction_count OR (correction_body.id=source_thread.last_observation_event_id
                        AND correction_body.payload->>'source_prefix_ref'=source_thread.source_prefix_ref))
                    AND correction_body.operation_id=correction_event.operation_id
                    AND correction_body.attempt_id=correction_event.attempt_id
                    AND (correction_step<>correction_count OR (
                        correction_body.operation_id::text=source_thread.data->>'operation_id'
                        AND correction_body.attempt_id::text=source_thread.data->>'attempt_id'))
                    AND correction_target.seq<correction_event.seq AND correction_event.seq<correction_body.seq
                    AND correction_target.recorded_at<=(correction_source->>'recorded_at')::timestamptz
                    AND correction_target.recorded_at<=correction_event.recorded_at
                    AND (correction_source->>'recorded_at')::timestamptz<=correction_event.recorded_at
                    AND correction_event.recorded_at<=correction_body.recorded_at
                    AND correction_body.recorded_at<=clock_timestamp()
                    AND NOT (correction_target.payload ? 'meaning_checkpoint_ref')
                    AND NOT (correction_body.payload ? 'meaning_checkpoint_ref')
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                correction_excerpt := correction_source->>'target_text';
                correction_target_text := correction_target.payload->>'text';
                correction_excerpt_at := strpos(correction_target_text,correction_excerpt);
                IF correction_excerpt_at<1 OR strpos(substr(correction_target_text,
                    correction_excerpt_at+1),correction_excerpt)>0 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                -- Exact compact metadata, with no normalization of either
                -- explanation or quoted AI locator. The separate raw frame
                -- contains only the person's explanation as evidence text.
                correction_header := '{"correction_id":'||(correction_source->'correction_id')::text
                    ||',"explanation":'||(correction_source->'explanation')::text
                    ||',"original_source_ref":'||(correction_source->'original_source_ref')::text
                    ||',"recorded_at":'||(correction_source->'recorded_at')::text
                    ||',"source_role":'||(correction_source->'source_role')::text
                    ||',"target_event_id":'||(correction_source->'target_event_id')::text
                    ||',"target_text":'||(correction_source->'target_text')::text
                    ||',"thread_id":'||(correction_source->'thread_id')::text||'}';
                -- Each historical prefix is BASE + the full ordered history
                -- through this source, never a recursive corrected-prefix hash.
                correction_headers := correction_headers || CASE WHEN correction_step=1 THEN '' ELSE ',' END || correction_header;
                correction_prefix := 'emlis-corrected-source-prefix-'||encode(sha256(convert_to(
                    '['||to_jsonb(correction_base_prefix)::text||',['||correction_headers||']]','UTF8')),'hex');
                IF correction_body.payload->>'source_prefix_ref' IS DISTINCT FROM correction_prefix
                    OR (correction_step=correction_count AND source_thread.source_prefix_ref IS DISTINCT FROM correction_prefix) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_frame := 'memo:'||octet_length(convert_to(correction_source->>'explanation','UTF8'))::text
                    ||':'||(correction_source->>'explanation')||'memo_action:0:';
                IF correction_step=correction_count AND (r.source_lineage#>>'{interpretation_correction_source,correction_id}'=correction_event.id::text
                    AND r.source_lineage#>>'{interpretation_correction_source,target_event_id}'=correction_target.id::text
                    AND r.source_lineage#>>'{interpretation_correction_source,source_version}'=
                        'sha256:'||encode(sha256(convert_to(correction_header,'UTF8')),'hex')
                    AND r.source_lineage#>>'{interpretation_correction_source,explanation_commitment}'=
                        'sha256:'||encode(sha256(convert_to(correction_frame,'UTF8')),'hex')
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                -- Exact compact array serialization of the existing identity(
                -- 'context', tier, guards, feedback); only typed scalar arrays
                -- enter this digest, so no whitespace is removed from strings.
                natural_guards := coalesce(source_thread.data->'context_guards','[]'::jsonb);
                natural_feedback := coalesce(source_thread.data->'context_feedback','[]'::jsonb);
                IF jsonb_typeof(natural_guards) IS DISTINCT FROM 'array'
                   OR jsonb_typeof(natural_feedback) IS DISTINCT FROM 'array' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF EXISTS (SELECT 1 FROM jsonb_array_elements(natural_guards) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>3
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->2) IS DISTINCT FROM 'number'
                          OR (x.value->>2) !~ '^(0|[1-9][0-9]*)$' END)
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(natural_feedback) x(value)
                    WHERE CASE WHEN jsonb_typeof(x.value) IS DISTINCT FROM 'array' THEN true
                        ELSE jsonb_array_length(x.value)<>2
                          OR jsonb_typeof(x.value->0) IS DISTINCT FROM 'string'
                          OR jsonb_typeof(x.value->1) IS DISTINCT FROM 'number'
                          OR (x.value->>1) !~ '^(0|[1-9][0-9]*)$' END) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||','||(x.value->2)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_guard_header
                    FROM jsonb_array_elements(natural_guards) WITH ORDINALITY x(value,ordinality);
                SELECT '['||coalesce(string_agg('['||(x.value->0)::text||','
                    ||(x.value->1)::text||']',',' ORDER BY x.ordinality),'')||']'
                    INTO natural_feedback_header
                    FROM jsonb_array_elements(natural_feedback) WITH ORDINALITY x(value,ordinality);
                natural_context_ref := 'context-'||encode(sha256(convert_to(
                    '['||to_jsonb(tier)::text||','||natural_guard_header||','||natural_feedback_header||']',
                    'UTF8')),'hex');
                IF jsonb_array_length(coalesce(source_thread.data->'frame_target_dependencies','[]'::jsonb))>0 THEN
                    SELECT '['||coalesce(string_agg(to_jsonb(
                        (x.value->>0)||':'||(x.value->>1)||':'||(x.value->>2)||':'||
                        (x.value->>3)||':'||(x.value->>4)||':'||(x.value->>5))::text,
                        ',' ORDER BY x.ordinality),'')||']' INTO natural_target_tokens
                        FROM jsonb_array_elements(source_thread.data->'frame_target_dependencies') WITH ORDINALITY x(value,ordinality);
                    natural_context_ref := 'context-frame-targets-'||encode(sha256(convert_to(
                        '['||to_jsonb(natural_context_ref)::text||','||natural_target_tokens||']','UTF8')),'hex');
                END IF;
                -- Same receipt and completion checks as the natural arm,
                -- with FINAL response_stage and no fictitious question/checkpoint.
                FOR natural_body IN SELECT e.* FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id
                      AND e.id IN (correction_target.id,correction_body.id) ORDER BY e.seq LOOP
                    natural_prefix := natural_body.payload->>'source_prefix_ref';
                    IF (natural_body.operation_id IS NOT NULL AND natural_body.attempt_id IS NOT NULL
                        AND natural_body.question_id IS NULL
                        AND natural_body.payload->>'context_ref'=natural_context_ref
                        AND natural_body.payload->'context_guards'=natural_guards
                        AND jsonb_typeof(natural_body.payload->'text')='string'
                        AND length(btrim(natural_body.payload->>'text'))>0
                        AND natural_body.payload#>>'{artifact,schema_version}'='cocolon.emlis.recipient_reply.v1'
                        AND natural_body.payload#>'{artifact,text}'=natural_body.payload->'text'
                        AND jsonb_typeof(natural_body.payload#>'{artifact,model}')='string'
                        AND length(btrim(natural_body.payload#>>'{artifact,model}'))>0
                        AND public.piece_natural_analysis_artifact_valid(natural_body.payload->'artifact',
                            natural_prefix,source_thread.user_id,source_thread.source_snapshot)
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED')<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED')<>1
                       OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.operation_id=natural_body.operation_id
                        AND e.attempt_id=natural_body.attempt_id AND e.payload->>'status'='COMPLETED'
                        AND e.payload->>'failure_code' IS NULL)<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT e.* INTO natural_started FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'stage'='NATURAL_REPLY_CALL_STARTED';
                    SELECT e.* INTO natural_received FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'stage'='NATURAL_REPLY_RECEIVED';
                    SELECT e.* INTO correction_finish FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.operation_id=natural_body.operation_id AND e.attempt_id=natural_body.attempt_id
                        AND e.payload->>'status'='COMPLETED' AND e.payload->>'failure_code' IS NULL;
                    IF (natural_started.round_index=0 AND natural_received.round_index=0
                        AND correction_finish.round_index=0 AND natural_body.round_index=0
                        AND natural_started.payload->>'source_prefix_ref'=natural_prefix
                        AND natural_received.payload->>'source_prefix_ref'=natural_prefix
                        AND natural_started.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_received.payload->>'context_ref'=natural_body.payload->>'context_ref'
                        AND natural_started.payload->>'response_stage'='FINAL'
                        AND natural_received.payload->>'response_stage'='FINAL'
                        AND natural_received.payload->'reply'=jsonb_build_object('text',natural_body.payload->'text',
                            'model',natural_body.payload#>'{artifact,model}','source_prefix_ref',natural_prefix,
                            'schema_version','cocolon.emlis.recipient_reply.v1')
                        AND natural_started.seq<natural_received.seq AND natural_received.seq<natural_body.seq
                        AND natural_body.seq<correction_finish.seq
                        AND source_created AT TIME ZONE 'UTC'<=natural_started.recorded_at
                        AND natural_started.recorded_at<=natural_received.recorded_at
                        AND natural_received.recorded_at<=natural_body.recorded_at
                        AND natural_body.recorded_at<=correction_finish.recorded_at
                        AND correction_finish.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF natural_body.id=correction_target.id THEN
                        IF correction_finish.seq>=correction_event.seq
                           OR correction_finish.recorded_at>(correction_source->>'recorded_at')::timestamptz THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                    ELSIF correction_event.seq>=natural_started.seq
                       OR correction_event.recorded_at>natural_started.recorded_at THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END LOOP;
                correction_previous_id := correction_body.id;
                correction_previous_prefix := correction_prefix;
                END LOOP;
                END IF;
$new$;
        IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
            RAISE EXCEPTION 'PIECE_MIXED_SOURCE_PRECONDITION';
        END IF;
        definition:=replace(definition,old_text,new_text);
        EXECUTE definition;
    END LOOP;
END;
$migration$;
COMMIT;
