-- Retain the admitted effective source state across genuine natural rounds.
-- Only the private all-prefix expectation selects this arm. Existing ADD and
-- latest-only update expectations keep their previous validation unchanged.
-- No event, source, saved lineage, RPC signature, lock or ACL is rewritten.
BEGIN;
DO $migration$
DECLARE
  signature text; definition text; arm text; a integer; b integer;
  old_text text; new_text text;
BEGIN
  FOREACH signature IN ARRAY ARRAY[
    'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
    'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
    'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
  ] LOOP
    definition := pg_get_functiondef(signature::regprocedure);
    old_text := $old$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage','meaning_checkpoint']='{}'::jsonb
            AND (NOT (p_expected_source_state ? 'meaning_checkpoint')
                OR jsonb_typeof(p_expected_source_state->'meaning_checkpoint')='object')$old$;
    new_text := $new$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage','meaning_checkpoint','meaning_checkpoints']='{}'::jsonb
            AND (NOT (p_expected_source_state ? 'meaning_checkpoint')
                OR jsonb_typeof(p_expected_source_state->'meaning_checkpoint')='object')
            AND (NOT (p_expected_source_state ? 'meaning_checkpoints')
                OR (jsonb_typeof(p_expected_source_state->'meaning_checkpoints')='array'
                    AND NOT (p_expected_source_state ? 'meaning_checkpoint')))$new$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_STATE_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    old_text := '        chain_envelope_ref text;';
    new_text := $new$        chain_envelope_ref text;
        effective_round_sources boolean;
        effective_has_prior_update boolean;
        effective_accepted jsonb;
        effective_inactive jsonb;
        effective_claim_sources jsonb;
        effective_claim_anchors jsonb;
        effective_claim_times jsonb;
        effective_item jsonb;
        effective_temporal jsonb;
        effective_ref text;
        effective_target text;
        effective_anchor text;
        effective_ref_kind text;$new$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_DECLARATION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    a := strpos(definition,$anchor$                IF source_thread.data->>'response_profile'='natural_reply.v1' THEN$anchor$);
    b := strpos(definition,$anchor$                ELSIF source_thread.data->>'response_profile' IS NULL THEN$anchor$);
    IF a=0 OR b<=a THEN RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_PRECONDITION'; END IF;
    arm := substr(definition,a,b-a);

    -- This exact preimage belongs to the 051948/074058 latest-update fence.
    -- Wrap it rather than weakening its old expectation or original anchor.
    old_text := $old$                IF p_expected_source_state ? 'meaning_checkpoint'$old$;
    new_text := $new$                IF p_expected_source_state ? 'meaning_checkpoints' THEN
                    IF (CASE WHEN jsonb_typeof(p_expected_source_state->'meaning_checkpoints')='array' THEN
                        source_thread.issued_count IN (2,3)
                        AND NOT (p_expected_source_state ? 'meaning_checkpoint')
                        AND jsonb_array_length(p_expected_source_state->'meaning_checkpoints')=source_thread.issued_count
                        AND p_expected_source_state->'meaning_checkpoints'->(source_thread.issued_count-1)=refined_checkpoint.payload
                    ELSE false END) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                ELSE
                IF p_expected_source_state ? 'meaning_checkpoint'$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_LATEST_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);
    -- The natural arm contains both refined and chain frame comments. Pin
    -- this boundary to the selected-answer assignment, which occurs once.
    old_text := $old$                refined_header := '{"answer_id":'||(refined_payload->'answer_id')::text$old$;
    new_text := $new$                END IF;
                refined_header := '{"answer_id":'||(refined_payload->'answer_id')::text$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_LATEST_END_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);

    old_text := $old$                -- Prior rounds establish eligibility, not extra Piece sources.$old$;
    new_text := $new$                -- Prior rounds establish eligibility, not extra Piece sources.
                effective_round_sources := coalesce(p_expected_source_state ? 'meaning_checkpoints',false);
                effective_has_prior_update := false;
                effective_accepted := '[]'::jsonb;
                effective_inactive := '[]'::jsonb;
                effective_claim_sources := '{}'::jsonb;
                effective_claim_anchors := '{}'::jsonb;
                effective_claim_times := '{}'::jsonb;$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_CHAIN_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);

    old_text := $old$                chain_update := chain_checkpoint.payload->'answer_update';$old$;
    new_text := $new$                IF effective_round_sources THEN
                    IF (jsonb_typeof(chain_checkpoint.payload)='object'
                        AND chain_checkpoint.payload ?& ARRAY['checkpoint_id','source_prefix_ref','base_meaning_ref',
                            'answer_update','assessment_status','accepted_update_refs','inactive_claim_refs',
                            'unresolved_parts','semantic_schema_version']
                        AND chain_checkpoint.payload-ARRAY['checkpoint_id','source_prefix_ref','base_meaning_ref',
                            'answer_update','assessment_status','accepted_update_refs','inactive_claim_refs',
                            'unresolved_parts','semantic_schema_version']='{}'::jsonb
                        AND chain_checkpoint.payload=p_expected_source_state->'meaning_checkpoints'->(chain_round-1)
                        AND chain_checkpoint.payload->>'checkpoint_id' ~ '^emlis-checkpoint-[0-9a-f]{64}$'
                        AND chain_checkpoint.payload->>'base_meaning_ref' ~ '^emlis-base-meaning-[0-9a-f]{64}$'
                        AND jsonb_typeof(chain_checkpoint.payload->'accepted_update_refs')='array'
                        AND jsonb_typeof(chain_checkpoint.payload->'inactive_claim_refs')='array'
                        AND chain_checkpoint.payload->>'source_prefix_ref'=chain_observation.payload->>'source_prefix_ref'
                        AND (chain_round<>source_thread.issued_count
                            OR (chain_checkpoint.id=source_thread.current_meaning_event_id
                                AND chain_checkpoint.id=refined_checkpoint.id
                                AND chain_observation.id=source_thread.last_observation_event_id
                                AND chain_answer.id=source_thread.latest_answer_event_id))
                    ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                END IF;
                chain_update := chain_checkpoint.payload->'answer_update';$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_CHECKPOINT_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);

    old_text := $old$                IF chain_round<source_thread.issued_count AND (jsonb_array_length(chain_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(chain_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                )) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;$old$;
    new_text := $new$                IF NOT effective_round_sources THEN
                IF chain_round<source_thread.issued_count AND (jsonb_array_length(chain_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(chain_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                )) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                END IF;$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_PRIOR_FENCE_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);

    -- Run only after the unchanged UTF-8 answer envelope calculation and
    -- answer_source_ref equality. The maps below track actual introduced
    -- claims, their time anchors, and every inactive dependency by prefix.
    old_text := $old$                IF chain_update->>'answer_source_ref' IS DISTINCT FROM chain_envelope_ref THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;$old$;
    new_text := $new$                IF chain_update->>'answer_source_ref' IS DISTINCT FROM chain_envelope_ref THEN
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
                END IF;$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_UPDATE_BINDING_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);

    old_text := $old$                    chain_previous_finish := chain_finish;
                  END LOOP;
                END IF;$old$;
    new_text := $new$                    chain_previous_finish := chain_finish;
                  END LOOP;
                  IF effective_round_sources AND NOT effective_has_prior_update THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                  END IF;
                END IF;$new$;
    IF (length(arm)-length(replace(arm,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_EFFECTIVE_SOURCE_CHAIN_END_CHANGED';
    END IF;
    arm := replace(arm,old_text,new_text);
    EXECUTE substr(definition,1,a-1)||arm||substr(definition,b);
  END LOOP;
END;
$migration$;
COMMIT;
