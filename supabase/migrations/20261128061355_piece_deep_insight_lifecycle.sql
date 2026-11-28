-- A record-derived DeepInsight answer has a different provenance contract from
-- an Emlis observation. Keep the existing Piece write and quota owners.
BEGIN;

CREATE FUNCTION public.piece_deep_insight_lineage_valid(p_lineage jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog AS $$
    SELECT coalesce(
        jsonb_typeof(p_lineage)='object'
        AND p_lineage ?& ARRAY['handoff_contract_version','piece_source_lineage_version','source_kind',
            'source_input','deep_insight','semantic_source_roles','body_free']
        AND p_lineage - ARRAY['handoff_contract_version','piece_source_lineage_version','source_kind',
            'source_input','deep_insight','semantic_source_roles','body_free']='{}'::jsonb
        AND p_lineage->>'handoff_contract_version'='cocolon.cross_core.source_handoff.v1'
        AND p_lineage->>'piece_source_lineage_version'='piece.source_lineage.v1'
        AND p_lineage->>'source_kind'='deep_insight_record_answer'
        AND p_lineage->'semantic_source_roles'='["original_input","deep_insight_answer"]'::jsonb
        AND p_lineage->'body_free'='true'::jsonb
        AND jsonb_typeof(p_lineage->'source_input')='object'
        AND (p_lineage->'source_input') ?& ARRAY['source_input_id','source_input_version',
            'source_input_bundle_commitment','source_owner_user_id','source_recorded_at']
        AND (p_lineage->'source_input') - ARRAY['source_input_id','source_input_version',
            'source_input_bundle_commitment','source_owner_user_id','source_recorded_at']='{}'::jsonb
        AND p_lineage#>>'{source_input,source_input_id}' ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
        AND p_lineage#>>'{source_input,source_owner_user_id}' ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
        AND p_lineage#>>'{source_input,source_input_version}'='emlis.current_input_bundle.v1'
        AND p_lineage#>>'{source_input,source_input_bundle_commitment}' ~ '^sha256:[0-9a-f]{64}$'
        AND p_lineage#>>'{source_input,source_recorded_at}' ~
            '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|\+00:00)$'
        AND jsonb_typeof(p_lineage->'deep_insight')='object'
        AND (p_lineage->'deep_insight') ?& ARRAY['deep_insight_question_id','source_version','source_commitment']
        AND (p_lineage->'deep_insight') - ARRAY['deep_insight_question_id','source_version','source_commitment']='{}'::jsonb
        AND p_lineage#>>'{deep_insight,deep_insight_question_id}' ~
            '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
        AND p_lineage#>>'{deep_insight,deep_insight_question_id}' <> p_lineage#>>'{source_input,source_input_id}'
        AND p_lineage#>>'{deep_insight,source_version}'='piece.deep_insight_answer.v1'
        AND p_lineage#>>'{deep_insight,source_commitment}' ~ '^sha256:[0-9a-f]{64}$',false);
$$;

CREATE FUNCTION public.piece_deep_insight_draft_state_valid(p_state jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog AS $$
    SELECT coalesce(jsonb_typeof(p_state)='object' AND p_state ?& ARRAY['original','lineage']
        AND p_state - ARRAY['original','lineage']='{}'::jsonb
        AND jsonb_typeof(p_state->'original')='object'
        AND public.piece_deep_insight_lineage_valid(p_state->'lineage'),false);
$$;

CREATE FUNCTION public.piece_lock_deep_insight_draft(p_owner uuid,p_lineage jsonb)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE
    resolved jsonb;
BEGIN
    IF NOT public.piece_deep_insight_lineage_valid(p_lineage)
       OR p_lineage#>>'{source_input,source_owner_user_id}' IS DISTINCT FROM p_owner::text THEN
        RAISE EXCEPTION 'PIECE_CONFLICT';
    END IF;
    resolved := public.piece_deep_insight_source_binding(p_owner,
        (p_lineage#>>'{source_input,source_input_id}')::uuid,
        (p_lineage#>>'{deep_insight,deep_insight_question_id}')::uuid,
        p_lineage#>>'{deep_insight,source_commitment}');
    IF resolved->>'subscription_tier' IS DISTINCT FROM 'premium'
       OR (p_lineage#>>'{source_input,source_recorded_at}')::timestamptz IS DISTINCT FROM
          (resolved#>>'{original,created_at}')::timestamp AT TIME ZONE 'UTC' THEN
        RAISE EXCEPTION 'PIECE_CONFLICT';
    END IF;
    RETURN resolved->'original';
EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow THEN
    RAISE EXCEPTION 'PIECE_CONFLICT';
END;
$$;

REVOKE ALL ON FUNCTION public.piece_deep_insight_lineage_valid(jsonb),
    public.piece_deep_insight_draft_state_valid(jsonb), public.piece_lock_deep_insight_draft(uuid,jsonb)
    FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.piece_deep_insight_lineage_valid(jsonb) TO service_role;

DO $resolver_and_checks$
DECLARE
    definition text;
    constraint_name text;
    existing_check text;
    deep_insight_check text;
    old_tier text := $old$if not found or tier not in ('free','plus','premium') or tier is null$old$;
    old_safety text := $old$or thread.data->>'body_state'='SAFETY'$old$;
    old_answer_count text := $old$(select count(*) from public.emlis_thread_events e where e.thread_id=thread.id and e.kind='ANSWER')>=2$old$;
    old_after_lock text := $old$or question.answered_at>=as_of then return null; end if;$old$;
BEGIN
    definition := pg_get_functiondef('public.piece_deep_insight_source_binding(uuid,uuid,uuid,text)'::regprocedure);
    IF (length(definition)-length(replace(definition,old_tier,'')))<>length(old_tier)
       OR (length(definition)-length(replace(definition,old_safety,'')))<>length(old_safety)
       OR (length(definition)-length(replace(definition,old_answer_count,'')))<>length(old_answer_count)
       OR (length(definition)-length(replace(definition,old_after_lock,'')))<>length(old_after_lock) THEN
        RAISE EXCEPTION 'PIECE_DEEP_INSIGHT_RESOLVER_PRECONDITION';
    END IF;
    definition := replace(definition,old_tier,$new$if not found or tier is distinct from 'premium'$new$);
    definition := replace(definition,old_safety,old_safety||$new$
    or thread.data->>'failure_code' in ('safe_state_answer_owner_required','separate_safety_owner_required')$new$);
    -- An Emlis answer may have superseded a clause of the original. This
    -- two-source contract has no slot for such a revision.
    definition := replace(definition,old_answer_count,$new$exists(select 1 from public.emlis_thread_events e
      where e.thread_id=thread.id and e.kind='ANSWER')$new$);
    EXECUTE replace(definition,old_after_lock,$new$then return null; end if;
  as_of:=clock_timestamp();
  if question.answered_at>=as_of or public.emlis_parent_visible(parent.created_at,tier,as_of) is not true
    then return null; end if;$new$);
    ALTER FUNCTION public.piece_deep_insight_source_binding(uuid,uuid,uuid,text) SET TimeZone TO 'UTC';

    FOREACH constraint_name IN ARRAY ARRAY['piece_records_lineage_binding','piece_records_source_stage',
        'piece_records_supplemental_boundary'] LOOP
        SELECT pg_get_expr(c.conbin,c.conrelid) INTO STRICT existing_check FROM pg_constraint c
        WHERE c.conrelid='public.piece_records'::regclass AND c.contype='c' AND c.conname=constraint_name;
        deep_insight_check := $new$source_lineage->>'source_kind' IS NOT DISTINCT FROM 'deep_insight_record_answer'$new$;
        IF constraint_name='piece_records_lineage_binding' THEN
            deep_insight_check := $new$public.piece_deep_insight_lineage_valid(source_lineage)
                AND source_lineage->>'piece_source_lineage_version'=source_lineage_version
                AND source_lineage#>>'{source_input,source_input_id}'=source_input_id
                AND source_lineage#>>'{source_input,source_input_version}'=source_input_version
                AND source_lineage#>>'{source_input,source_input_bundle_commitment}'=source_input_bundle_commitment
                AND source_lineage#>>'{source_input,source_owner_user_id}'=owner_user_id::text$new$;
        END IF;
        EXECUTE format('ALTER TABLE public.piece_records DROP CONSTRAINT %1$I,
            ADD CONSTRAINT %1$I CHECK (((%2$s) OR (%3$s)) IS TRUE)',
            constraint_name,existing_check,deep_insight_check);
    END LOOP;
END;
$resolver_and_checks$;

DO $piece_writers$
DECLARE
    signature text;
    definition text;
    legacy_guard text;
    old_boundary text;
    new_boundary text;
    legacy_thread text := $old$        IF p_expected_source_state IS NOT NULL THEN
            SELECT t.* INTO source_thread FROM public.emlis_input_threads t$old$;
    typed_thread text := $new$        IF r.source_lineage->>'source_kind'='deep_insight_record_answer' THEN
            IF p_expected_subscription_tier IS DISTINCT FROM 'premium' OR tier IS DISTINCT FROM 'premium'
               OR NOT public.piece_deep_insight_draft_state_valid(p_expected_source_state)
               OR r.source_lineage IS DISTINCT FROM p_expected_source_state->'lineage' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF public.piece_lock_deep_insight_draft(p_owner_user_id,r.source_lineage)
                IS DISTINCT FROM source_snapshot THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
        ELSIF p_expected_source_state IS NOT NULL THEN
            SELECT t.* INTO source_thread FROM public.emlis_input_threads t$new$;
BEGIN
    FOREACH signature IN ARRAY ARRAY[
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)',
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)'
    ] LOOP
        definition := pg_get_functiondef(signature::regprocedure);
        legacy_guard := substring(definition FROM
            $pattern$jsonb_typeof\(p_expected_source_state\)='object'.+?\(p_expected_source_state->>'thread_revision'\) ~ '\^\[1-9\]\[0-9\]\*\$'$pattern$);
        IF legacy_guard IS NULL OR (length(definition)-length(replace(definition,legacy_thread,'')))<>length(legacy_thread)
           OR (length(definition)-length(replace(definition,legacy_guard,'')))<>length(legacy_guard) THEN
            RAISE EXCEPTION 'PIECE_DEEP_INSIGHT_WRITER_PRECONDITION';
        END IF;
        definition := replace(definition,legacy_guard,
            '(public.piece_deep_insight_draft_state_valid(p_expected_source_state) OR ('||legacy_guard||'))');
        EXECUTE replace(definition,legacy_thread,typed_thread);
    END LOOP;

    -- The low-level compatibility writer remains callable and must independently
    -- reject an invalid typed issue or replay, including a mismatched old shape.
    definition := pg_get_functiondef('public.piece_issue_preview_v2(uuid,text,text,jsonb,integer)'::regprocedure);
    old_boundary := $old$            replayed := true;
        ELSE$old$;
    new_boundary := $new$            IF coalesce(r.source_lineage->>'source_kind','')='deep_insight_record_answer'
               OR coalesce(p_record#>>'{source_lineage,source_kind}','')='deep_insight_record_answer' THEN
                IF r.source_lineage IS DISTINCT FROM p_record->'source_lineage' THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                PERFORM public.piece_lock_deep_insight_draft(p_owner_user_id,r.source_lineage);
                IF r.expires_at<=clock_timestamp() THEN RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED'; END IF;
            END IF;
            replayed := true;
        ELSE$new$;
    IF (length(definition)-length(replace(definition,old_boundary,'')))<>length(old_boundary) THEN
        RAISE EXCEPTION 'PIECE_DEEP_INSIGHT_ISSUE_REPLAY_PRECONDITION';
    END IF;
    definition := replace(definition,old_boundary,new_boundary);
    old_boundary := $old$            at_time := clock_timestamp();
            INSERT INTO public.piece_records$old$;
    new_boundary := $new$            IF p_record#>>'{source_lineage,source_kind}'='deep_insight_record_answer' THEN
                PERFORM public.piece_lock_deep_insight_draft(p_owner_user_id,p_record->'source_lineage');
            END IF;
            at_time := clock_timestamp();
            INSERT INTO public.piece_records$new$;
    IF (length(definition)-length(replace(definition,old_boundary,'')))<>length(old_boundary) THEN
        RAISE EXCEPTION 'PIECE_DEEP_INSIGHT_ISSUE_PRECONDITION';
    END IF;
    EXECUTE replace(definition,old_boundary,new_boundary);
END;
$piece_writers$;

COMMIT;
