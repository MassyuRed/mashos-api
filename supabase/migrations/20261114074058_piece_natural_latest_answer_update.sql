-- Latest round2/3 may revise or withdraw one ORIGINAL clause.
-- Earlier rounds remain ADD-only eligibility controls, never extra Piece sources.
-- Signatures, locks, source lineage, RLS and ACLs remain unchanged.
BEGIN;
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
    old_text := $old0$IF (source_thread.issued_count=1
                        AND p_expected_source_state$old0$;
    new_text := $new0$IF (source_thread.issued_count IN (1,2,3)
                        AND p_expected_source_state$new0$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_LATEST_UPDATE_DEFINITION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    old_text := $old1$AND refined_checkpoint.payload->'accepted_update_refs'=jsonb_build_array(item->>'update_ref')$old1$;
    new_text := $new1$AND refined_checkpoint.payload->'accepted_update_refs'=(
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
                                )$new1$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_LATEST_UPDATE_DEFINITION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    old_text := $old2$IF jsonb_array_length(chain_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(chain_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                ) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;$old2$;
    new_text := $new2$IF chain_round=source_thread.issued_count AND (
                    chain_checkpoint.id IS DISTINCT FROM refined_checkpoint.id
                    OR chain_checkpoint.payload IS DISTINCT FROM refined_checkpoint.payload
                ) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                IF chain_round<source_thread.issued_count AND (jsonb_array_length(chain_update->'updates')<1 OR EXISTS (
                    SELECT 1 FROM jsonb_array_elements(chain_update->'updates') item
                    WHERE (jsonb_typeof(item)='object' AND item->>'operation'='ADD'
                        AND item->'superseded_claim_refs'='[]'::jsonb
                        AND item->'affected_dependency_refs'='[]'::jsonb) IS NOT TRUE
                )) THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;$new2$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_LATEST_UPDATE_DEFINITION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    definition := replace(definition,
        '-- Only the current one-answer checkpoint is extended.',
        '-- Only the selected latest exact-clause checkpoint is extended.');
    definition := replace(definition,
        '-- Later rounds below still require the unchanged ADD chain.',
        '-- Earlier rounds below still require the unchanged ADD chain.');
    EXECUTE definition;
  END LOOP;
END;
$migration$;
COMMIT;
