-- Natural replies can now carry private, source-grounded Analysis material.
-- Piece still uses only the unchanged saved input and the selected answer.
-- Python rederives the full material; these transactional fences bind that
-- state to the persisted observation, owner, original snapshot and prefix.
BEGIN;

CREATE FUNCTION public.piece_natural_analysis_artifact_valid(
    p_artifact jsonb, p_source_prefix text, p_owner uuid, p_original jsonb
) RETURNS boolean LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path='' AS $$
SELECT coalesce(CASE
  WHEN NOT (p_artifact ? 'analysis_material') THEN
    p_artifact->>'analysis_state'='NOT_GENERATED'
    AND NOT (p_artifact ? 'meaning_profile')
  ELSE
    p_artifact->>'meaning_profile'='source_grounded_active_meaning.v1'
    AND p_artifact->>'analysis_state' IN ('GENERATED','NOT_GENERATED')
    AND jsonb_typeof(p_artifact->'analysis_material')='object'
    AND p_artifact#>>'{analysis_material,schema_version}'='cocolon.cmee.emlis_analysis_material.v1'
    AND p_artifact#>>'{analysis_material,state}'=p_artifact->>'analysis_state'
    AND p_artifact#>>'{analysis_material,source_prefix_ref}'=p_source_prefix
    AND p_artifact#>>'{analysis_material,owner_scope}'=p_owner::text
    AND p_artifact#>>'{analysis_material,record_ref}'=p_original->>'id'
    AND p_artifact#>'{analysis_material,original_record}'=p_original
    AND p_artifact#>>'{analysis_material,record_version}' ~ '^sha256:[0-9a-f]{64}$'
    AND p_artifact#>>'{analysis_material,material_ref}' ~ '^emlis-analysis-material:[0-9a-f]{64}$'
    AND p_artifact#>>'{analysis_material,graph_scope}'='ANALYSIS_SOURCE_GROUNDED_INTERPRETATION'
    AND p_artifact#>>'{analysis_material,coverage,active_state}' IN ('RESOLVED','PENDING')
    AND jsonb_typeof(p_artifact#>'{analysis_material,active_fields}')='array'
    AND jsonb_typeof(p_artifact#>'{analysis_material,sources}')='array'
END, false);
$$;
REVOKE ALL ON FUNCTION public.piece_natural_analysis_artifact_valid(jsonb,text,uuid,jsonb)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.piece_natural_analysis_artifact_valid(jsonb,text,uuid,jsonb)
  TO service_role;

DO $migration$
DECLARE signature text; definition text; old_text text; new_text text;
BEGIN
  FOREACH signature IN ARRAY ARRAY[
    'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
    'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
    'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)'
  ] LOOP
    definition := pg_get_functiondef(signature::regprocedure);
    old_text := $old$OR source_thread.data->>'analysis_state' IS DISTINCT FROM 'NOT_GENERATED'$old$;
    new_text := $new$OR NOT coalesce(source_thread.data->>'analysis_state' IN ('GENERATED','NOT_GENERATED'),false)
                   OR (source_thread.data->>'analysis_state'='GENERATED'
                       AND source_thread.data->>'natural_meaning_profile' IS DISTINCT FROM 'source_grounded_active_meaning.v1')$new$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_SHARED_MEANING_DEFINITION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    old_text := $old$AND natural_body.payload#>>'{artifact,analysis_state}'='NOT_GENERATED'$old$;
    new_text := $new$AND public.piece_natural_analysis_artifact_valid(
                            natural_body.payload->'artifact',natural_prefix,
                            source_thread.user_id,source_thread.source_snapshot)$new$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_SHARED_MEANING_DEFINITION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    old_text := $old$AND chain_observation.payload#>>'{artifact,analysis_state}'='NOT_GENERATED'$old$;
    new_text := $new$AND public.piece_natural_analysis_artifact_valid(
                            chain_observation.payload->'artifact',chain_observation.payload->>'source_prefix_ref',
                            source_thread.user_id,source_thread.source_snapshot)$new$;
    IF (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 THEN
      RAISE EXCEPTION 'PIECE_SHARED_MEANING_DEFINITION_CHANGED';
    END IF;
    definition := replace(definition,old_text,new_text);
    EXECUTE definition;
  END LOOP;
END;
$migration$;
COMMIT;
