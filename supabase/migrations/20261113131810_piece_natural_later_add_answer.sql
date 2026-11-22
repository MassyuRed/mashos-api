-- Latest explicitly selected ADD only; prior rounds are eligibility controls.
-- Existing source locks, history/frame dependencies, signatures and ACLs remain.
BEGIN;
DO $migration$
DECLARE
  signature text; definition text; arm text; prefix text; suffix text; a integer; b integer;
BEGIN
  FOREACH signature IN ARRAY ARRAY['public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
    'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
    'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'] LOOP
    definition := pg_get_functiondef(signature::regprocedure);
    a := strpos(definition,$anchor$                IF source_thread.data->>'response_profile'='natural_reply.v1' THEN$anchor$);
    b := strpos(definition,$anchor$                ELSIF source_thread.data->>'response_profile' IS NULL THEN$anchor$);
    IF a=0 OR b<=a THEN RAISE EXCEPTION 'PIECE_LATER_ADD_PRECONDITION'; END IF;
    prefix := substr(definition,1,a-1); arm := substr(definition,a,b-a); suffix := substr(definition,b);
    IF (length(arm)-length(replace(arm,$old$source_thread.issued_count IS DISTINCT FROM 1$old$,'')))/length($old$source_thread.issued_count IS DISTINCT FROM 1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$source_thread.issued_count IS DISTINCT FROM 1$old$,$new$source_thread.issued_count NOT IN (1,2,3)$new$);
    IF (length(arm)-length(replace(arm,$old$e.kind='ANSWER')<>1$old$,'')))/length($old$e.kind='ANSWER')<>1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$e.kind='ANSWER')<>1$old$,$new$e.kind='ANSWER')<>source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$e.kind='QUESTION')<>1$old$,'')))/length($old$e.kind='QUESTION')<>1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$e.kind='QUESTION')<>1$old$,$new$e.kind='QUESTION')<>source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$e.kind='MEANING_UPDATE')<>1$old$,'')))/length($old$e.kind='MEANING_UPDATE')<>1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$e.kind='MEANING_UPDATE')<>1$old$,$new$e.kind='MEANING_UPDATE')<>source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$e.kind='OBSERVATION')<>2$old$,'')))/length($old$e.kind='OBSERVATION')<>2$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$e.kind='OBSERVATION')<>2$old$,$new$e.kind='OBSERVATION')<>source_thread.issued_count+1$new$);
    IF (length(arm)-length(replace(arm,$old$'NATURAL_REPLY_RECEIVED'))<>4$old$,'')))/length($old$'NATURAL_REPLY_RECEIVED'))<>4$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$'NATURAL_REPLY_RECEIVED'))<>4$old$,$new$'NATURAL_REPLY_RECEIVED'))<>2*(source_thread.issued_count+1)$new$);
    IF (length(arm)-length(replace(arm,$old$refined_answer.round_index=1$old$,'')))/length($old$refined_answer.round_index=1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_answer.round_index=1$old$,$new$refined_answer.round_index=source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$refined_payload->'round_index'='1'::jsonb$old$,'')))/length($old$refined_payload->'round_index'='1'::jsonb$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_payload->'round_index'='1'::jsonb$old$,$new$refined_payload->'round_index'=to_jsonb(source_thread.issued_count)$new$);
    IF (length(arm)-length(replace(arm,$old$refined_question.round_index=1$old$,'')))/length($old$refined_question.round_index=1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_question.round_index=1$old$,$new$refined_question.round_index=source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$refined_observation.round_index=1$old$,'')))/length($old$refined_observation.round_index=1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_observation.round_index=1$old$,$new$refined_observation.round_index=source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$refined_checkpoint.round_index IS DISTINCT FROM 1$old$,'')))/length($old$refined_checkpoint.round_index IS DISTINCT FROM 1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_checkpoint.round_index IS DISTINCT FROM 1$old$,$new$refined_checkpoint.round_index IS DISTINCT FROM source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$natural_finish.round_index=1$old$,'')))/length($old$natural_finish.round_index=1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$natural_finish.round_index=1$old$,$new$natural_finish.round_index=source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$natural_terminal.round_index=1$old$,'')))/length($old$natural_terminal.round_index=1$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$natural_terminal.round_index=1$old$,$new$natural_terminal.round_index=source_thread.issued_count$new$);
    IF (length(arm)-length(replace(arm,$old$natural_initial.seq<refined_question.seq$old$,'')))/length($old$natural_initial.seq<refined_question.seq$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$natural_initial.seq<refined_question.seq$old$,$new$natural_initial.seq<natural_first_question.seq$new$);
    IF (length(arm)-length(replace(arm,$old$refined_question.operation_id=natural_initial.operation_id$old$,'')))/length($old$refined_question.operation_id=natural_initial.operation_id$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_question.operation_id=natural_initial.operation_id$old$,$new$natural_first_question.operation_id=natural_initial.operation_id$new$);
    IF (length(arm)-length(replace(arm,$old$refined_question.attempt_id=natural_initial.attempt_id$old$,'')))/length($old$refined_question.attempt_id=natural_initial.attempt_id$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_question.attempt_id=natural_initial.attempt_id$old$,$new$natural_first_question.attempt_id=natural_initial.attempt_id$new$);
    IF (length(arm)-length(replace(arm,$old$natural_initial.recorded_at<=refined_question.recorded_at$old$,'')))/length($old$natural_initial.recorded_at<=refined_question.recorded_at$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$natural_initial.recorded_at<=refined_question.recorded_at$old$,$new$natural_initial.recorded_at<=natural_first_question.recorded_at$new$);
    IF (length(arm)-length(replace(arm,$old$refined_question.seq<natural_initial_finish.seq$old$,'')))/length($old$refined_question.seq<natural_initial_finish.seq$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_question.seq<natural_initial_finish.seq$old$,$new$natural_first_question.seq<natural_initial_finish.seq$new$);
    IF (length(arm)-length(replace(arm,$old$refined_question.recorded_at<=natural_initial_finish.recorded_at$old$,'')))/length($old$refined_question.recorded_at<=natural_initial_finish.recorded_at$old$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$old$refined_question.recorded_at<=natural_initial_finish.recorded_at$old$,$new$natural_first_question.recorded_at<=natural_initial_finish.recorded_at$new$);
    IF (length(arm)-length(replace(arm,$a$                SELECT e.* INTO natural_initial FROM public.emlis_thread_events e$a$,'')))/length($a$                SELECT e.* INTO natural_initial FROM public.emlis_thread_events e$a$)<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DEFINITION_CHANGED'; END IF;
    arm := replace(arm,$a$                SELECT e.* INTO natural_initial FROM public.emlis_thread_events e$a$,$b$                SELECT e.* INTO natural_first_question FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='QUESTION' AND e.round_index=1 FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                SELECT e.* INTO natural_initial FROM public.emlis_thread_events e$b$);
    IF (length(prefix)-length(replace(prefix,'        natural_target_tokens text;','')))/length('        natural_target_tokens text;')<>1 THEN RAISE EXCEPTION 'PIECE_LATER_ADD_DECLARATION_CHANGED'; END IF;
    prefix := replace(prefix,'        natural_target_tokens text;',$decl$        natural_target_tokens text;
        natural_first_question public.emlis_thread_events%ROWTYPE;
        chain_answer public.emlis_thread_events%ROWTYPE;
        chain_question public.emlis_thread_events%ROWTYPE;
        chain_checkpoint public.emlis_thread_events%ROWTYPE;
        chain_observation public.emlis_thread_events%ROWTYPE;
        chain_started public.emlis_thread_events%ROWTYPE;
        chain_received public.emlis_thread_events%ROWTYPE;
        chain_finish public.emlis_thread_events%ROWTYPE;
        chain_previous_finish public.emlis_thread_events%ROWTYPE;
        chain_continued public.emlis_thread_events%ROWTYPE;
        chain_round integer;
        chain_kind text;
        chain_stage text;
        chain_payload jsonb;
        chain_update jsonb;
        chain_header text;
        chain_frame_hash text;
        chain_envelope_ref text;$decl$);
    EXECUTE prefix||arm||$chain$                -- Prior rounds establish eligibility, not extra Piece sources.
                IF source_thread.issued_count>1 THEN
                  IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                    AND e.kind='OPERATION' AND e.payload->>'status'='CONTINUED')<>source_thread.issued_count-1 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                  END IF;
                  chain_previous_finish := natural_initial_finish;
                  FOR chain_round IN 1..source_thread.issued_count LOOP
                    FOREACH chain_kind IN ARRAY ARRAY['QUESTION','ANSWER','MEANING_UPDATE','OBSERVATION'] LOOP
                      IF (SELECT count(*) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id
                          AND e.kind=chain_kind AND e.round_index=chain_round)<>1 THEN
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
                      AND e.kind='OBSERVATION' AND e.round_index=chain_round FOR SHARE OF e;
                    chain_payload := chain_answer.payload->'source';
                IF (jsonb_typeof(chain_payload)='object'
                    AND chain_payload ?& ARRAY['answer_id','thread_id','question_id','round_index',
                        'original_source_ref','answer_text_private','recorded_at','authored_at',
                        'source_version','source_role']
                    AND chain_payload-ARRAY['answer_id','thread_id','question_id','round_index',
                        'original_source_ref','answer_text_private','recorded_at','authored_at',
                        'source_version','source_role']='{}'::jsonb
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
                chain_update := chain_checkpoint.payload->'answer_update';
                IF (jsonb_typeof(chain_update)='object'
                    AND chain_update->>'disposition'='MATERIAL_UPDATE'
                    AND chain_update->>'question_ref'=chain_question.question_id
                    AND chain_update->'unresolved_parts'='[]'::jsonb
                    AND jsonb_typeof(chain_update->'updates')='array'
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF jsonb_array_length(chain_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(chain_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                ) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
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
                        AND chain_observation.payload#>>'{artifact,analysis_state}'='NOT_GENERATED'
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
$chain$||suffix;
  END LOOP;
END;
$migration$;
COMMIT;
