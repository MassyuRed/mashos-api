-- Refined Piece source fence only. Apply through the existing migration owner.
-- No table/column/constraint/ACL/RLS/signature/quota/renderer change and no data
-- rewrite. Existing original/natural source fences and saved replay order stay.
-- A refined request still uses the canonical lineage and four-key expectation.
BEGIN;
DO $migration$
DECLARE
    target regprocedure;
    definition text;
    old_declaration text := '        q3_context boolean := false;';
    new_declaration text := $declaration$        refined_answer public.emlis_thread_events%ROWTYPE;
        refined_question public.emlis_thread_events%ROWTYPE;
        refined_checkpoint public.emlis_thread_events%ROWTYPE;
        refined_observation public.emlis_thread_events%ROWTYPE;
        refined_payload jsonb;
        refined_update jsonb;
        refined_header text;
        refined_frame_hash text;
        refined_envelope_ref text;
        q3_context boolean := false;$declaration$;
    old_guard text := $guard$               OR source_thread.latest_answer_event_id IS NOT NULL THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF source_thread.data->>'runtime_profile' = 'q3.plan.sequential.v1' THEN$guard$;
    new_guard text := $guard$               OR (r.source_lineage#>>'{observation,emlis_observation_stage}'
                    IS DISTINCT FROM 'refined_observation'
                   AND source_thread.latest_answer_event_id IS NOT NULL) THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF r.source_lineage#>>'{observation,emlis_observation_stage}'='refined_observation' THEN
                -- The existing original/profile/thread locks remain held.
                -- Read the committed answer, decision, checkpoint and result;
                -- none of their generated prose becomes Piece source material.
                IF source_thread.state IS DISTINCT FROM 'COMPLETED'
                   OR source_thread.active_attempt_id IS NOT NULL
                   OR source_thread.processing_deadline_at IS NOT NULL
                   OR source_thread.latest_answer_event_id::text IS DISTINCT FROM
                        r.source_lineage#>>'{observation,supplemental_answer_identity}'
                   OR source_thread.issued_count IS DISTINCT FROM 1
                   OR source_thread.evaluated_prefix_ref IS DISTINCT FROM source_thread.source_prefix_ref
                   OR coalesce(source_thread.data->>'runtime_profile','') NOT IN
                        ('q2.free.one_round.v1','q3.plan.sequential.v1')
                   OR source_thread.data->>'response_profile'='natural_reply.v1'
                   OR source_thread.data->>'semantic_profile' IS NOT NULL
                   OR source_thread.data->>'body_state' IS DISTINCT FROM 'REFINED'
                   OR source_thread.data->>'answer_assessment' IS DISTINCT FROM 'RESOLVED'
                   OR source_thread.data->'meaning_updated' IS DISTINCT FROM 'true'::jsonb
                   OR source_thread.data->>'failure_code' IS NOT NULL THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='ANSWER')<>1
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='QUESTION')<>1 THEN
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
                    WHERE e.id=source_thread.current_meaning_event_id AND e.thread_id=source_thread.id
                    FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO refined_observation FROM public.emlis_thread_events e
                    WHERE e.id=source_thread.last_observation_event_id AND e.thread_id=source_thread.id
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
                    AND refined_answer.kind='ANSWER' AND refined_answer.round_index=1
                    AND refined_payload->>'answer_id'=refined_answer.id::text
                    AND refined_payload->>'thread_id'=source_thread.id::text
                    AND refined_payload->'round_index'='1'::jsonb
                    AND refined_payload->>'source_role'='SUPPLEMENTAL_ANSWER'
                    AND refined_payload->>'source_version'='cocolon.cmee.supplemental_answer.v1'
                    AND refined_payload->>'source_version'=
                        r.source_lineage#>>'{observation,supplemental_answer_version}'
                    AND refined_payload->>'original_source_ref'=source_thread.data->>'original_source_ref'
                    AND jsonb_typeof(refined_payload->'answer_text_private')='string'
                    AND length(btrim(refined_payload->>'answer_text_private'))>0
                    AND jsonb_typeof(refined_payload->'recorded_at')='string'
                    AND jsonb_typeof(refined_payload->'authored_at') IN ('string','null')
                    AND refined_question.kind='QUESTION' AND refined_question.round_index=1
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
                    AND refined_checkpoint.payload->>'source_prefix_ref'=source_thread.source_prefix_ref
                    AND refined_checkpoint.payload->>'assessment_status'='RESOLVED'
                    AND refined_checkpoint.payload->'unresolved_parts'='[]'::jsonb
                    AND refined_observation.kind='OBSERVATION' AND refined_observation.round_index=1
                    AND refined_observation.payload->>'stage'='REFINED'
                    AND refined_observation.payload->>'source_prefix_ref'=source_thread.source_prefix_ref
                    AND refined_observation.payload->>'meaning_checkpoint_ref'=
                        refined_checkpoint.payload->>'checkpoint_id'
                    AND refined_answer.operation_id=refined_observation.operation_id
                    AND refined_answer.attempt_id=refined_observation.attempt_id
                    AND refined_checkpoint.operation_id=refined_observation.operation_id
                    AND refined_checkpoint.attempt_id=refined_observation.attempt_id
                    AND refined_observation.operation_id::text=source_thread.data->>'operation_id'
                    AND refined_observation.attempt_id::text=source_thread.data->>'attempt_id'
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.operation_id=refined_observation.operation_id
                      AND e.attempt_id=refined_observation.attempt_id
                      AND e.seq>refined_observation.seq AND e.payload->>'status'='COMPLETED'
                      AND e.payload->>'failure_code' IS NULL)<>1 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                refined_update := refined_checkpoint.payload->'answer_update';
                IF (jsonb_typeof(refined_update)='object'
                    AND refined_update->>'disposition'='MATERIAL_UPDATE'
                    AND refined_update->>'question_ref'=refined_question.question_id
                    AND refined_update->'unresolved_parts'='[]'::jsonb
                    AND jsonb_typeof(refined_update->'updates')='array'
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF jsonb_array_length(refined_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(refined_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                ) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                -- Exact compact, lexically sorted metadata JSON of the existing
                -- freeze_supplemental_answer owner. Byte length is UTF-8 length,
                -- not character count; text is not normalized or concatenated
                -- into the saved original. The resulting digest includes every
                -- answer identity/version/time/parent field and the exact body.
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
            END IF;
            IF source_thread.data->>'runtime_profile' = 'q3.plan.sequential.v1' THEN$guard$;
    signatures text[] := ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'];
    signature text;
BEGIN
    FOREACH signature IN ARRAY signatures LOOP
        target := to_regprocedure(signature);
        IF target IS NULL THEN RAISE EXCEPTION 'PIECE_REFINED_SOURCE_PRECONDITION'; END IF;
        definition := pg_get_functiondef(target);
        IF (length(definition)-length(replace(definition,old_declaration,'')))/length(old_declaration)<>1
           OR (length(definition)-length(replace(definition,old_guard,'')))/length(old_guard)<>1 THEN
            RAISE EXCEPTION 'PIECE_REFINED_SOURCE_DEFINITION_CHANGED';
        END IF;
        EXECUTE replace(replace(definition,old_declaration,new_declaration),old_guard,new_guard);
    END LOOP;
END;
$migration$;
COMMIT;
