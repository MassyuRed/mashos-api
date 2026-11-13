-- Current natural Q3 first-ANSWER ADD source fence for the three existing RPCs.
-- Precondition: 20261109024943_piece_refined_source_fence and existing natural
-- related-context migration. No table/ACL/RLS/signature/lock/quota/renderer edit.
-- Legacy refined guard remains byte-identical in the response_profile IS NULL
-- arm. Unknown response profiles fail closed.
-- SQL proves committed event/receipt/answer-envelope/context relationships.
-- It does NOT re-run Python admit_emlis_thread(original-only prefix), the
-- grounded base plan, or prepare_emlis_meaning's whole checkpoint derivation.
-- That stronger original-language re-derivation remains in the API adapter.
-- In particular, SQL checks initial prefix consistency across the initial
-- saved chain and difference from current prefix, rather than claiming an
-- independent original-only prefix derivation. AI text/model remain controls.
BEGIN;
DO $migration$
DECLARE
    target regprocedure;
    definition text;
    old_declaration text := $old_declaration$        refined_answer public.emlis_thread_events%ROWTYPE;
        refined_question public.emlis_thread_events%ROWTYPE;
        refined_checkpoint public.emlis_thread_events%ROWTYPE;
        refined_observation public.emlis_thread_events%ROWTYPE;
        refined_payload jsonb;
        refined_update jsonb;
        refined_header text;
        refined_frame_hash text;
        refined_envelope_ref text;
        q3_context boolean := false;$old_declaration$;
    new_declaration text := $new_declaration$        refined_answer public.emlis_thread_events%ROWTYPE;
        refined_question public.emlis_thread_events%ROWTYPE;
        refined_checkpoint public.emlis_thread_events%ROWTYPE;
        refined_observation public.emlis_thread_events%ROWTYPE;
        refined_payload jsonb;
        refined_update jsonb;
        refined_header text;
        refined_frame_hash text;
        refined_envelope_ref text;
        natural_initial public.emlis_thread_events%ROWTYPE;
        natural_body public.emlis_thread_events%ROWTYPE;
        natural_started public.emlis_thread_events%ROWTYPE;
        natural_received public.emlis_thread_events%ROWTYPE;
        natural_initial_finish public.emlis_thread_events%ROWTYPE;
        natural_finish public.emlis_thread_events%ROWTYPE;
        natural_terminal public.emlis_thread_events%ROWTYPE;
        natural_guards jsonb;
        natural_feedback jsonb;
        natural_guard_header text;
        natural_feedback_header text;
        natural_context_ref text;
        natural_prefix text;
        natural_response_stage text;
        natural_answer_at timestamptz;
        q3_context boolean := false;$new_declaration$;
    old_guard text := $old_guard$               OR (r.source_lineage#>>'{observation,emlis_observation_stage}'
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
            IF source_thread.data->>'runtime_profile' = 'q3.plan.sequential.v1' THEN$old_guard$;
    new_guard text := $new_guard$               OR (r.source_lineage#>>'{observation,emlis_observation_stage}'
                    IS DISTINCT FROM 'refined_observation'
                   AND source_thread.latest_answer_event_id IS NOT NULL) THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF r.source_lineage#>>'{observation,emlis_observation_stage}'='refined_observation' THEN
                IF source_thread.data->>'response_profile'='natural_reply.v1' THEN
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
                   OR source_thread.data->>'runtime_profile' IS DISTINCT FROM 'q3.plan.sequential.v1'
                   OR source_thread.data->>'response_profile' IS DISTINCT FROM 'natural_reply.v1'
                   OR source_thread.data->>'natural_question_policy' IS DISTINCT FROM 'native_bound_question.v1'
                   OR source_thread.data->>'analysis_state' IS DISTINCT FROM 'NOT_GENERATED'
                   OR source_thread.data->>'natural_response_stage' IS DISTINCT FROM 'REFINED'
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
                    AND NOT (refined_observation.payload ? 'meaning_checkpoint_ref')
                    AND refined_answer.operation_id=refined_observation.operation_id
                    AND refined_answer.attempt_id=refined_observation.attempt_id
                    AND refined_checkpoint.operation_id=refined_observation.operation_id
                    AND refined_checkpoint.attempt_id=refined_observation.attempt_id
                    AND refined_observation.operation_id::text=source_thread.data->>'operation_id'
                    AND refined_observation.attempt_id::text=source_thread.data->>'attempt_id'
                ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
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
                -- Natural replies have no initial semantic checkpoint and no
                -- synthetic meaning_checkpoint_ref on either OBSERVATION.
                IF (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='MEANING_UPDATE')<>1
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION')<>2
                   OR (SELECT count(*) FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage' IN ('NATURAL_REPLY_CALL_STARTED','NATURAL_REPLY_RECEIVED'))<>4
                   OR EXISTS (SELECT 1 FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OPERATION'
                      AND e.payload->>'stage'='INTERPRETATION_CORRECTION')
                   OR refined_checkpoint.round_index IS DISTINCT FROM 1
                   OR jsonb_typeof(refined_checkpoint.payload->'checkpoint_id') IS DISTINCT FROM 'string'
                   OR length(coalesce(refined_checkpoint.payload->>'checkpoint_id',''))=0 THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                SELECT e.* INTO natural_initial FROM public.emlis_thread_events e
                    WHERE e.thread_id=source_thread.id AND e.kind='OBSERVATION'
                      AND e.round_index=0 AND e.payload->>'stage'='INITIAL' FOR SHARE OF e;
                IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF (natural_initial.seq<refined_question.seq
                    AND natural_initial.operation_id IS NOT NULL AND natural_initial.attempt_id IS NOT NULL
                    AND refined_question.operation_id=natural_initial.operation_id
                    AND refined_question.attempt_id=natural_initial.attempt_id
                    AND natural_initial.payload->>'source_prefix_ref'<>source_thread.source_prefix_ref
                    AND NOT (natural_initial.payload ? 'meaning_checkpoint_ref')
                    AND natural_initial.recorded_at<=refined_question.recorded_at
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
                        AND natural_body.payload#>>'{artifact,analysis_state}'='NOT_GENERATED'
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
                IF (refined_question.seq<natural_initial_finish.seq
                    AND natural_initial_finish.seq<refined_answer.seq
                    AND natural_initial_finish.round_index=1
                    AND refined_question.recorded_at<=natural_initial_finish.recorded_at
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
                IF (refined_observation.seq<natural_finish.seq AND natural_finish.round_index=1
                    AND refined_observation.recorded_at<=natural_finish.recorded_at
                    AND natural_finish.recorded_at<=clock_timestamp()) IS NOT TRUE THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF source_thread.data->>'natural_question_stop'='stop' THEN
                    IF (SELECT count(*) FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL')<>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT e.* INTO natural_terminal FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL' FOR SHARE OF e;
                    IF (natural_finish.payload->>'status'='AWAITING_CONTINUE'
                        AND natural_terminal.payload->>'reason'='stop'
                        AND natural_terminal.round_index=1
                        AND natural_terminal.operation_id IS NULL AND natural_terminal.attempt_id IS NULL
                        AND natural_finish.seq<natural_terminal.seq
                        AND natural_terminal.seq=(SELECT max(e.seq) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id)
                        AND natural_finish.recorded_at<=natural_terminal.recorded_at
                        AND natural_terminal.recorded_at<=clock_timestamp()
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                ELSE
                    IF source_thread.data->>'natural_question_stop' IS NOT NULL
                       OR EXISTS (SELECT 1 FROM public.emlis_thread_events e
                        WHERE e.thread_id=source_thread.id AND e.kind='TERMINAL')
                       OR natural_finish.payload->>'status' IS DISTINCT FROM 'COMPLETED'
                       OR natural_finish.seq IS DISTINCT FROM
                            (SELECT max(e.seq) FROM public.emlis_thread_events e WHERE e.thread_id=source_thread.id) THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                END IF;
                ELSIF source_thread.data->>'response_profile' IS NULL THEN
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
                ELSE
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
            END IF;
            IF source_thread.data->>'runtime_profile' = 'q3.plan.sequential.v1' THEN$new_guard$;
    signatures text[] := ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'];
    signature text;
BEGIN
    FOREACH signature IN ARRAY signatures LOOP
        target := to_regprocedure(signature);
        IF target IS NULL THEN RAISE EXCEPTION 'PIECE_NATURAL_REFINED_SOURCE_PRECONDITION'; END IF;
        definition := pg_get_functiondef(target);
        IF (length(definition)-length(replace(definition,old_declaration,'')))/length(old_declaration)<>1
           OR (length(definition)-length(replace(definition,old_guard,'')))/length(old_guard)<>1 THEN
            RAISE EXCEPTION 'PIECE_NATURAL_REFINED_SOURCE_DEFINITION_CHANGED';
        END IF;
        EXECUTE replace(replace(definition,old_declaration,new_declaration),old_guard,new_guard);
    END LOOP;
END;
$migration$;
COMMIT;
