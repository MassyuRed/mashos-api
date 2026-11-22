-- Issued-preview visual mutation, SOURCE-ONLY CANDIDATE. No live application.
-- Authentication, current recipe selection and hash construction belong to the
-- server. This RPC binds that admitted result to the exact issued row and the
-- same original/profile/thread/consumed-context fence as M4. No text generation,
-- quota write, expiry extension, table ACL/RLS change or saved-record mutation.
DO $piece_preview_visual$
DECLARE
    acl_entry record;
    signature text := 'public.piece_mutate_preview_visual_v2(uuid,uuid,bigint,jsonb,jsonb,text,text,jsonb)';
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='service_role')
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles
                      WHERE rolname=current_user AND (rolsuper OR rolbypassrls))
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_class
            WHERE oid=pg_catalog.to_regclass('public.piece_records')
              AND relkind='r' AND relrowsecurity AND relforcerowsecurity)
       OR pg_catalog.to_regclass('public.profiles') IS NULL
       OR pg_catalog.to_regclass('public.emotions') IS NULL
       OR pg_catalog.to_regclass('public.emlis_input_threads') IS NULL
       OR pg_catalog.to_regclass('public.emlis_frame_feedback') IS NULL
       OR pg_catalog.to_regprocedure('public.piece_cancel_preview_v2(uuid,uuid,bigint)') IS NULL
       OR pg_catalog.to_regprocedure('public.emlis_thread_context(uuid,uuid)') IS NULL THEN
        RAISE EXCEPTION 'PIECE_PREVIEW_VISUAL_PRECONDITION';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        WHERE n.nspname='public' AND p.proname='piece_mutate_preview_visual_v2') THEN
        RAISE EXCEPTION 'PIECE_PREVIEW_VISUAL_TARGET_EXISTS';
    END IF;

    CREATE FUNCTION public.piece_mutate_preview_visual_v2(
        p_owner_user_id uuid, p_preview_id uuid, p_expected_preview_revision bigint,
        p_expected_record jsonb, p_visual_recipe jsonb, p_visual_recipe_hash text,
        p_expected_subscription_tier text, p_expected_source_state jsonb
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $mutate$
    DECLARE
        r public.piece_records%ROWTYPE;
        tier text;
        at_time timestamptz;
        fields text[] := ARRAY['id','owner_user_id','piece_contract_version','lifecycle_status',
            'preview_request_hash','preview_revision','row_version','expires_at',
            'visibility_scope','source_lineage','format_type','preview_eligible_formats',
            'content_payload','content_payload_hash','piece_text','piece_text_hash',
            'safety_state','visual_recipe','visual_recipe_hash','renderer_version'];
        row_snapshot jsonb;
        source_snapshot jsonb;
        source_created timestamp;
        source_thread record;
        q3_context boolean := false;
        context_guards jsonb;
        context_feedback jsonb;
        current_context jsonb;
        g jsonb;
        history_source record;
        history_thread record;
        history_times timestamp[] := ARRAY[]::timestamp[];
        history_time timestamp;
    BEGIN
        IF p_owner_user_id IS NULL OR p_owner_user_id='00000000-0000-0000-0000-000000000000'::uuid THEN
            RAISE EXCEPTION 'PIECE_AUTH_REQUIRED';
        END IF;
        IF p_preview_id IS NULL OR p_expected_preview_revision IS NULL OR p_expected_preview_revision<1
           OR p_visual_recipe_hash IS NULL OR p_visual_recipe_hash !~ '^[0-9a-f]{64}$'
           OR jsonb_typeof(p_visual_recipe) IS DISTINCT FROM 'object'
           OR (jsonb_typeof(p_expected_record)='object' AND p_expected_record ?& fields
            AND p_expected_record-fields='{}'::jsonb
            AND jsonb_typeof(p_expected_record->'expires_at')='string') IS NOT TRUE
           OR p_expected_subscription_tier IS NULL
           OR p_expected_subscription_tier NOT IN ('free','plus','premium')
           OR (jsonb_typeof(p_expected_source_state)='object'
            AND p_expected_source_state ?& ARRAY['original','thread_id','thread_revision','lineage']
            AND p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage']='{}'::jsonb
            AND jsonb_typeof(p_expected_source_state->'original')='object'
            AND jsonb_typeof(p_expected_source_state->'lineage')='object'
            AND jsonb_typeof(p_expected_source_state->'thread_id')='string'
            AND jsonb_typeof(p_expected_source_state->'thread_revision')='number'
            AND (p_expected_source_state->>'thread_revision') ~ '^[1-9][0-9]*$'
           ) IS NOT TRUE THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        SELECT * INTO r FROM public.piece_records
            WHERE id=p_preview_id AND owner_user_id=p_owner_user_id FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
        IF r.lifecycle_status<>'preview_draft' OR r.visibility_scope<>'private' THEN
            RAISE EXCEPTION 'PIECE_CONFLICT';
        END IF;
        IF r.preview_revision<>p_expected_preview_revision THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_STALE';
        END IF;
        IF r.expires_at IS NULL OR r.expires_at<=clock_timestamp() THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED';
        END IF;
        SELECT jsonb_object_agg(k,to_jsonb(r)->k) INTO row_snapshot FROM unnest(fields) k;
        -- PostgREST and PostgreSQL may spell the same timestamptz differently.
        -- Only the expiry representation is normalized; all other values must
        -- equal the complete server read snapshot, including canonical content.
        IF row_snapshot-'expires_at' IS DISTINCT FROM p_expected_record-'expires_at'
           OR r.expires_at IS DISTINCT FROM (p_expected_record->>'expires_at')::timestamptz
           OR r.preview_request_hash IS NULL OR r.preview_eligible_formats IS NULL THEN
            RAISE EXCEPTION 'PIECE_CONFLICT';
        END IF;
        -- Keep the shared source owner's lock order: original -> profile ->
        -- thread. These are reads only, bound to the authenticated server
        -- snapshot. This overload requires a complete server expectation.
        IF p_expected_source_state IS NOT NULL THEN
            IF r.source_lineage IS DISTINCT FROM p_expected_source_state->'lineage' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            SELECT public.emlis_parent_source(e), e.created_at
                INTO source_snapshot, source_created FROM public.emotions e
                WHERE e.id::text=r.source_input_id AND e.user_id=p_owner_user_id FOR SHARE OF e;
            IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
            IF source_snapshot IS DISTINCT FROM p_expected_source_state->'original' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
        END IF;
        SELECT subscription_tier INTO tier FROM public.profiles
            WHERE id=p_owner_user_id FOR SHARE;
        tier := CASE WHEN tier IN ('free','plus','premium') THEN tier ELSE 'free' END;
        IF p_expected_subscription_tier IS NOT NULL
           AND tier IS DISTINCT FROM p_expected_subscription_tier THEN
            RAISE EXCEPTION 'PIECE_CONFLICT';
        END IF;
        IF p_expected_source_state IS NOT NULL THEN
            SELECT t.* INTO source_thread FROM public.emlis_input_threads t
                WHERE t.original_emotion_id::text=r.source_input_id
                  AND t.user_id=p_owner_user_id FOR SHARE OF t;
            IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
            IF source_thread.id::text IS DISTINCT FROM p_expected_source_state->>'thread_id'
               OR source_thread.revision::text IS DISTINCT FROM p_expected_source_state->>'thread_revision'
               OR source_thread.source_snapshot IS DISTINCT FROM source_snapshot
               OR source_thread.last_observation_event_id::text IS DISTINCT FROM
                    r.source_lineage#>>'{observation,emlis_observation_result_identity}'
               OR source_thread.state NOT IN ('COMPLETED','AWAITING_ANSWER')
               OR source_thread.active_operation_id IS NOT NULL
               OR source_thread.latest_answer_event_id IS NOT NULL THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF source_thread.data->>'runtime_profile' = 'q3.plan.sequential.v1' THEN
                q3_context := true;
                context_guards := coalesce(source_thread.data->'context_guards','[]'::jsonb);
                context_feedback := coalesce(source_thread.data->'context_feedback','[]'::jsonb);
                IF jsonb_typeof(context_guards) IS DISTINCT FROM 'array'
                   OR jsonb_typeof(context_feedback) IS DISTINCT FROM 'array'
                   OR coalesce(source_thread.data->'evaluated_tier',to_jsonb(tier)) IS DISTINCT FROM to_jsonb(tier) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                IF jsonb_array_length(context_guards) >
                    (CASE tier WHEN 'premium' THEN 6 WHEN 'plus' THEN 3 ELSE 0 END) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
                -- Match the Q3 writer's profile -> thread -> sorted history
                -- order. The profile SHARE lock serializes the established
                -- Emlis thread/feedback writers (which take profile UPDATE).
                -- Guarded history rows also protect against direct source
                -- edits/deletes. No history body enters the Piece record.
                FOR g IN SELECT value FROM jsonb_array_elements(context_guards) ORDER BY value->>0 LOOP
                    IF jsonb_typeof(g) IS DISTINCT FROM 'array' THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    IF jsonb_array_length(g) <> 3 OR jsonb_typeof(g->0) IS DISTINCT FROM 'string'
                       OR jsonb_typeof(g->1) IS DISTINCT FROM 'string'
                       OR jsonb_typeof(g->2) IS DISTINCT FROM 'number'
                       OR (g->>2) !~ '^(0|[1-9][0-9]*)$' THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT h.id,h.created_at,md5(public.emlis_parent_source(h)::text) AS source_hash
                        INTO history_source FROM public.emotions h
                        WHERE h.id::text=g->>0 AND h.user_id=p_owner_user_id FOR SHARE OF h;
                    IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
                    IF history_source.id::text=r.source_input_id
                       OR (history_source.created_at,history_source.id) >= (source_created,r.source_input_id::uuid)
                       OR history_source.source_hash IS DISTINCT FROM g->>1 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    SELECT ht.revision INTO history_thread FROM public.emlis_input_threads ht
                        WHERE ht.original_emotion_id=history_source.id AND ht.user_id=p_owner_user_id
                        FOR SHARE OF ht;
                    IF coalesce(history_thread.revision,0)::text IS DISTINCT FROM g->>2 THEN
                        RAISE EXCEPTION 'PIECE_CONFLICT';
                    END IF;
                    history_times := array_append(history_times,history_source.created_at);
                END LOOP;
                IF tier='premium' THEN
                    -- Existing feedback updates/deletes (including source
                    -- cascade) wait here; new feedback through the Q3 owner
                    -- is serialized by the profile lock above.
                    PERFORM 1 FROM public.emlis_frame_feedback f WHERE f.user_id=p_owner_user_id
                        ORDER BY f.frame_key FOR SHARE OF f;
                END IF;
            END IF;
        END IF;
        -- No quota/month lock or text generation: sample time after every
        -- admission lock wait and recheck the source's visible lifetime.
        at_time := clock_timestamp();
        IF p_expected_source_state IS NOT NULL THEN
            IF public.emlis_parent_visible(source_created,tier,at_time) IS NOT TRUE THEN
                RAISE EXCEPTION 'PIECE_NOT_FOUND';
            END IF;
        END IF;
        IF q3_context THEN
            -- Q3's read owner uses statement time. Explicitly check consumed
            -- rows with the post-wait clock so a preview/source wait cannot keep
            -- an expired historical input eligible.
            FOREACH history_time IN ARRAY history_times LOOP
                IF public.emlis_parent_visible(history_time,tier,at_time) IS NOT TRUE
                   OR history_time < at_time AT TIME ZONE 'UTC' -
                        (CASE WHEN tier='premium' THEN interval '3650 days' ELSE interval '365 days' END) THEN
                    RAISE EXCEPTION 'PIECE_CONFLICT';
                END IF;
            END LOOP;
            -- Reuse current Q3 selection semantics, including history limits,
            -- answer resolution and the exact feedback version vector.
            current_context := public.emlis_thread_context(p_owner_user_id,r.source_input_id::uuid);
            IF jsonb_typeof(current_context->'history') IS DISTINCT FROM 'array'
               OR jsonb_typeof(current_context->'feedback') IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF EXISTS (SELECT 1 FROM jsonb_array_elements(context_guards) expected
                WHERE NOT EXISTS (SELECT 1 FROM jsonb_array_elements(current_context->'history') live
                    WHERE live->'guard'=expected))
               OR context_feedback IS DISTINCT FROM coalesce((SELECT jsonb_agg(
                    jsonb_build_array(f->'frame_key',f->'version') ORDER BY f->>'frame_key')
                    FROM jsonb_array_elements(current_context->'feedback') f),'[]'::jsonb) THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
        END IF;
        -- Recheck the preview after every source/context wait. Time spent
        -- waiting never grants a fresh lifetime or revives an expired draft.
        IF r.expires_at<=at_time THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED';
        END IF;
        UPDATE public.piece_records SET visual_recipe=p_visual_recipe,
            visual_recipe_hash=p_visual_recipe_hash,
            preview_revision=preview_revision+1,row_version=row_version+1,
            updated_at=at_time WHERE id=r.id RETURNING * INTO r;
        RETURN jsonb_build_object('preview_id',r.id,'preview_revision',r.preview_revision,
            'row_version',r.row_version,'expires_at',r.expires_at,'visibility_scope',r.visibility_scope,
            'format_type',r.format_type,'eligible_formats',r.preview_eligible_formats,
            'content_payload',r.content_payload,'content_payload_hash',r.content_payload_hash,
            'piece_text',r.piece_text,'piece_text_hash',r.piece_text_hash,'safety_state',r.safety_state,
            'visual_recipe',r.visual_recipe,'visual_recipe_hash',r.visual_recipe_hash,
            'renderer_version',r.renderer_version,'idempotency_replayed',false);
    EXCEPTION WHEN check_violation OR not_null_violation OR invalid_text_representation
        OR invalid_datetime_format OR datetime_field_overflow OR numeric_value_out_of_range THEN
        RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
    END;
    $mutate$;

    EXECUTE 'REVOKE ALL ON FUNCTION ' || signature || ' FROM PUBLIC, anon, authenticated, service_role';
    -- Remove inherited function default ACLs without touching those defaults,
    -- or any existing table privileges/policies.
    FOR acl_entry IN SELECT DISTINCT roles.rolname
        FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,
            pg_catalog.acldefault('f',p.proowner))) a
        JOIN pg_catalog.pg_roles roles ON roles.oid=a.grantee
        WHERE p.oid=signature::regprocedure AND a.grantee<>p.proowner
    LOOP
        EXECUTE format('REVOKE ALL ON FUNCTION %s FROM %I',signature,acl_entry.rolname);
    END LOOP;
    EXECUTE 'GRANT EXECUTE ON FUNCTION ' || signature || ' TO service_role';
END;
$piece_preview_visual$;
