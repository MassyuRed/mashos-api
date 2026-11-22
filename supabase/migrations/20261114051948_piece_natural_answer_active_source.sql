-- One genuine natural answer may carry one resolved exact-clause update.
-- Semantic/range admission stays with the shared meaning and Piece owners.
-- These existing writers retain their source locks, replay order and ACLs.
BEGIN;
DO $migration$
DECLARE
  signature text; definition text; arm text; a integer; b integer;
  old_fence text := $old$                IF jsonb_array_length(refined_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(refined_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                ) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;$old$;
  active_fence text := $new$                IF p_expected_source_state ? 'meaning_checkpoint'
                    AND p_expected_source_state->'meaning_checkpoint' IS DISTINCT FROM refined_checkpoint.payload THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF (jsonb_array_length(refined_update->'updates')>=1 AND NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements(refined_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                )) IS NOT TRUE THEN
                    -- Only the current one-answer checkpoint is extended.
                    -- Later rounds below still require the unchanged ADD chain.
                    IF (source_thread.issued_count=1
                        AND p_expected_source_state->'meaning_checkpoint'=refined_checkpoint.payload
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
                                AND refined_checkpoint.payload->'accepted_update_refs'=jsonb_build_array(item->>'update_ref')
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
                END IF;$new$;
BEGIN
  FOREACH signature IN ARRAY ARRAY[
    'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
    'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
    'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
  ] LOOP
    definition := pg_get_functiondef(signature::regprocedure);
    IF (length(definition)-length(replace(definition,
        $shape$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage']='{}'::jsonb$shape$,'')))
        /length($shape$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage']='{}'::jsonb$shape$)<>1 THEN
      RAISE EXCEPTION 'PIECE_ACTIVE_ANSWER_STATE_CHANGED';
    END IF;
    definition := replace(definition,
      $shape$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage']='{}'::jsonb$shape$,
      $shape$p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage','meaning_checkpoint']='{}'::jsonb
            AND (NOT (p_expected_source_state ? 'meaning_checkpoint')
                OR jsonb_typeof(p_expected_source_state->'meaning_checkpoint')='object')$shape$);
    a := strpos(definition,$anchor$                IF source_thread.data->>'response_profile'='natural_reply.v1' THEN$anchor$);
    b := strpos(definition,$anchor$                ELSIF source_thread.data->>'response_profile' IS NULL THEN$anchor$);
    IF a=0 OR b<=a THEN RAISE EXCEPTION 'PIECE_ACTIVE_ANSWER_PRECONDITION'; END IF;
    arm := substr(definition,a,b-a);
    IF strpos(arm,'source_thread.issued_count NOT IN (1,2,3)')=0
       OR strpos(arm,'-- Prior rounds establish eligibility, not extra Piece sources.')=0
       OR (length(arm)-length(replace(arm,old_fence,'')))/length(old_fence)<>1 THEN
      RAISE EXCEPTION 'PIECE_ACTIVE_ANSWER_DEFINITION_CHANGED';
    END IF;
    EXECUTE substr(definition,1,a-1)||replace(arm,old_fence,active_fence)||substr(definition,b);
  END LOOP;
END;
$migration$;
COMMIT;
