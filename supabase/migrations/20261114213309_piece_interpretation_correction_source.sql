-- Carry one saved two-input interpretation correction into the current Piece.
-- Original fields, person explanation and AI target remain separate sources.
-- Only existing lineage checks and the three source-fenced writer overloads
-- change; locks, clocks, quotas, public signatures and ACLs stay unchanged.
BEGIN;
ALTER TABLE public.piece_records
    DROP CONSTRAINT piece_records_lineage_binding,
    DROP CONSTRAINT piece_records_source_stage,
    ADD CONSTRAINT piece_records_lineage_binding CHECK ((
            jsonb_typeof(source_lineage) = 'object'
            AND source_lineage ?& ARRAY['handoff_contract_version','piece_source_lineage_version',
                'source_input','observation','semantic_source_roles','lineage_control_roles',
                'piece_generation_eligibility','body_free']
            AND (source_lineage-'interpretation_correction_source') - ARRAY['handoff_contract_version','piece_source_lineage_version',
                'source_input','observation','semantic_source_roles','lineage_control_roles',
                'piece_generation_eligibility','body_free'] = '{}'::jsonb
            AND source_lineage->>'handoff_contract_version' = 'cocolon.cross_core.source_handoff.v1'
            AND source_lineage->>'piece_source_lineage_version' = source_lineage_version
            AND source_lineage->'body_free' = 'true'::jsonb
            AND jsonb_typeof(source_lineage->'source_input') = 'object'
            AND (source_lineage->'source_input') ?& ARRAY['source_input_id','source_input_version',
                'source_input_bundle_commitment','source_owner_user_id','source_recorded_at']
            AND (source_lineage->'source_input') - ARRAY['source_input_id','source_input_version',
                'source_input_bundle_commitment','source_owner_user_id','source_recorded_at'] = '{}'::jsonb
            AND source_lineage#>>'{source_input,source_input_id}' = source_input_id
            AND source_lineage#>>'{source_input,source_input_version}' = source_input_version
            AND source_lineage#>>'{source_input,source_input_bundle_commitment}' = source_input_bundle_commitment
            AND source_lineage#>>'{source_input,source_owner_user_id}' = owner_user_id::text
            AND jsonb_typeof(source_lineage#>'{source_input,source_recorded_at}') = 'string'
            AND length(source_lineage#>>'{source_input,source_recorded_at}') > 0
            AND jsonb_typeof(source_lineage->'observation') = 'object'
            AND (source_lineage->'observation') ?& ARRAY['emlis_observation_stage',
                'emlis_observation_result_identity','emlis_observation_result_state',
                'question_need_decision_identity','supplemental_answer_identity',
                'supplemental_answer_version','supplemental_answer_bundle_commitment']
            AND (source_lineage->'observation') - ARRAY['emlis_observation_stage',
                'emlis_observation_result_identity','emlis_observation_result_state',
                'question_need_decision_identity','supplemental_answer_identity',
                'supplemental_answer_version','supplemental_answer_bundle_commitment'] = '{}'::jsonb
            AND jsonb_typeof(source_lineage#>'{observation,emlis_observation_result_identity}') = 'string'
            AND length(source_lineage#>>'{observation,emlis_observation_result_identity}') > 0
            AND source_lineage#>>'{observation,emlis_observation_result_state}' = 'terminal_success'
            AND jsonb_typeof(source_lineage->'piece_generation_eligibility') = 'object'
            AND (source_lineage->'piece_generation_eligibility') ?& ARRAY['contract_version','decision','reason_codes']
            AND (source_lineage->'piece_generation_eligibility') - ARRAY['contract_version','decision','reason_codes'] = '{}'::jsonb
            AND source_lineage#>>'{piece_generation_eligibility,contract_version}' = 'piece.generation_eligibility.v1'
            AND source_lineage#>>'{piece_generation_eligibility,decision}' = 'eligible'
            AND jsonb_typeof(source_lineage#>'{piece_generation_eligibility,reason_codes}') = 'array'
            AND CASE WHEN source_lineage#>>'{observation,emlis_observation_stage}'='corrected_observation' THEN
                jsonb_typeof(source_lineage->'interpretation_correction_source')='object'
                AND (source_lineage->'interpretation_correction_source') ?& ARRAY[
                    'correction_id','source_version','explanation_commitment','target_event_id']
                AND (source_lineage->'interpretation_correction_source')-ARRAY[
                    'correction_id','source_version','explanation_commitment','target_event_id']='{}'::jsonb
                AND source_lineage#>>'{interpretation_correction_source,correction_id}' ~
                    '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                AND source_lineage#>>'{interpretation_correction_source,target_event_id}' ~
                    '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                AND source_lineage#>>'{interpretation_correction_source,source_version}' ~ '^sha256:[0-9a-f]{64}$'
                AND source_lineage#>>'{interpretation_correction_source,explanation_commitment}' ~ '^sha256:[0-9a-f]{64}$'
            ELSE NOT (source_lineage ? 'interpretation_correction_source') END
        ) IS TRUE),
    ADD CONSTRAINT piece_records_source_stage CHECK ((
            (source_lineage#>>'{observation,emlis_observation_stage}' = 'normal_observation'
                AND source_lineage->'semantic_source_roles' = '["original_input"]'::jsonb
                AND source_lineage->'lineage_control_roles' = '["emlis_observation_result"]'::jsonb
                AND source_lineage#>'{observation,question_need_decision_identity}' = 'null'::jsonb)
            OR (source_lineage#>>'{observation,emlis_observation_stage}' IN ('pre_question_observation','refined_observation')
                AND source_lineage->'lineage_control_roles' = '["emlis_observation_result","question_need_decision"]'::jsonb
                AND jsonb_typeof(source_lineage#>'{observation,question_need_decision_identity}') = 'string'
                AND length(source_lineage#>>'{observation,question_need_decision_identity}') > 0
                AND source_lineage->'semantic_source_roles' = CASE
                    WHEN source_lineage#>>'{observation,emlis_observation_stage}' = 'refined_observation'
                    THEN '["original_input","supplemental_answer"]'::jsonb ELSE '["original_input"]'::jsonb END)
            OR (source_lineage#>>'{observation,emlis_observation_stage}'='corrected_observation'
                AND source_lineage->'semantic_source_roles'='["original_input","interpretation_correction"]'::jsonb
                AND source_lineage->'lineage_control_roles'='["emlis_observation_result","ai_interpretation_target"]'::jsonb
                AND source_lineage#>'{observation,question_need_decision_identity}'='null'::jsonb)
        ) IS TRUE);
DO $migration$
DECLARE
    signature text; definition text; old_text text; new_text text;
BEGIN
    FOREACH signature IN ARRAY ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
    ] LOOP
        definition := pg_get_functiondef(signature::regprocedure);
        old_text := $old$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage','meaning_checkpoint','meaning_checkpoints']='{}'::jsonb
            AND (NOT (p_expected_source_state ? 'meaning_checkpoint')
                OR jsonb_typeof(p_expected_source_state->'meaning_checkpoint')='object')
            AND (NOT (p_expected_source_state ? 'meaning_checkpoints')
                OR (jsonb_typeof(p_expected_source_state->'meaning_checkpoints')='array'
                    AND NOT (p_expected_source_state ? 'meaning_checkpoint')))$old$;
        new_text := $new$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage','meaning_checkpoint','meaning_checkpoints','interpretation_correction']='{}'::jsonb
            AND (NOT (p_expected_source_state ? 'meaning_checkpoint')
                OR jsonb_typeof(p_expected_source_state->'meaning_checkpoint')='object')
            AND (NOT (p_expected_source_state ? 'meaning_checkpoints')
                OR (jsonb_typeof(p_expected_source_state->'meaning_checkpoints')='array'
                    AND NOT (p_expected_source_state ? 'meaning_checkpoint')))
            AND CASE WHEN p_expected_source_state#>>'{lineage,observation,emlis_observation_stage}'='corrected_observation' THEN
                jsonb_typeof(p_expected_source_state->'interpretation_correction')='object'
                AND NOT (p_expected_source_state ? 'meaning_checkpoint')
                AND NOT (p_expected_source_state ? 'meaning_checkpoints')
            ELSE NOT (p_expected_source_state ? 'interpretation_correction') END$new$;
        IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
            RAISE EXCEPTION 'PIECE_CORRECTION_EXPECTATION_PRECONDITION';
        END IF;
        definition := replace(definition,old_text,new_text);
        old_text := '        q3_context boolean := false;';
        new_text := $new$        correction_expected jsonb;
        correction_source jsonb;
        correction_events jsonb;
        correction_event public.emlis_thread_events%ROWTYPE;
        correction_target public.emlis_thread_events%ROWTYPE;
        correction_body public.emlis_thread_events%ROWTYPE;
        correction_finish public.emlis_thread_events%ROWTYPE;
        correction_header text;
        correction_frame text;
        correction_excerpt text;
        correction_target_text text;
        correction_excerpt_at integer;
        q3_context boolean := false;$new$;
        IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
            RAISE EXCEPTION 'PIECE_CORRECTION_DECLARATION_PRECONDITION';
        END IF;
        definition := replace(definition,old_text,new_text);
        old_text := $old$            IF r.source_lineage#>>'{observation,emlis_observation_stage}'='refined_observation' THEN$old$;
        new_text := $new$            IF r.source_lineage#>>'{observation,emlis_observation_stage}'='corrected_observation' THEN
                -- A real two-input correction is neither an ANSWER nor an
                -- INITIAL-only source. Lock the exact accepted source prefix.
                correction_expected := p_expected_source_state->'interpretation_correction';
                correction_source := correction_expected->'source';
                IF (jsonb_typeof(correction_expected)='object'
                    AND correction_expected ?& ARRAY['source','source_prefix_ref','events','thread_data']
                    AND correction_expected-ARRAY['source','source_prefix_ref','events','thread_data']='{}'::jsonb
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
                        AND e.kind='OBSERVATION')<>2
                   OR (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                        AND e.kind='OPERATION' AND e.payload->>'stage'='INTERPRETATION_CORRECTION')<>1 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO correction_event FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage'='INTERPRETATION_CORRECTION';
                SELECT e.* INTO correction_target FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.id::text=correction_source->>'target_event_id';
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO correction_body FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.id=source_thread.last_observation_event_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (correction_event.id::text=correction_source->>'correction_id'
                    AND correction_event.round_index=0 AND correction_event.question_id IS NULL
                    AND correction_event.payload->'source'=correction_source
                    AND correction_event.payload->>'status'='SAVED'
                    AND correction_event.payload->>'assessment'='UNASSESSED'
                    AND correction_event.idempotency_key IS NOT NULL
                    AND correction_event.operation_id IS NOT NULL AND correction_event.attempt_id IS NOT NULL
                    AND correction_target.kind='OBSERVATION' AND correction_target.round_index=0
                    AND correction_target.payload->>'stage'='INITIAL'
                    AND correction_target.payload->>'source_prefix_ref' ~ '^emlis-q3-source-prefix-[0-9a-f]{64}$'
                    AND correction_target.payload->>'source_prefix_ref'<>source_thread.source_prefix_ref
                    AND correction_body.kind='OBSERVATION' AND correction_body.round_index=0
                    AND correction_body.payload->>'stage'='CORRECTED'
                    AND correction_body.payload->>'source_prefix_ref'=source_thread.source_prefix_ref
                    AND correction_body.operation_id=correction_event.operation_id
                    AND correction_body.attempt_id=correction_event.attempt_id
                    AND correction_body.operation_id::text=source_thread.data->>'operation_id'
                    AND correction_body.attempt_id::text=source_thread.data->>'attempt_id'
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
                -- Re-derive the corrected prefix from the admitted Q3 prefix
                -- and this ordered proper source; the AI reply is not input.
                IF source_thread.source_prefix_ref IS DISTINCT FROM
                    'emlis-corrected-source-prefix-'||encode(sha256(convert_to(
                        '['||(correction_target.payload->'source_prefix_ref')::text
                        ||',['||correction_header||']]','UTF8')),'hex') THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                correction_frame := 'memo:'||octet_length(convert_to(correction_source->>'explanation','UTF8'))::text
                    ||':'||(correction_source->>'explanation')||'memo_action:0:';
                IF (r.source_lineage#>>'{interpretation_correction_source,correction_id}'=correction_event.id::text
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
                           OR correction_finish.recorded_at>correction_event.recorded_at THEN
                            RAISE EXCEPTION 'PIECE_CONFLICT';
                        END IF;
                    ELSIF correction_event.seq>=natural_started.seq
                       OR correction_event.recorded_at>natural_started.recorded_at THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END LOOP;
            ELSIF r.source_lineage#>>'{observation,emlis_observation_stage}'='refined_observation' THEN$new$;
        IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
            RAISE EXCEPTION 'PIECE_CORRECTION_ARM_PRECONDITION';
        END IF;
        EXECUTE replace(definition,old_text,new_text);
    END LOOP;
END;
$migration$;
COMMIT;
