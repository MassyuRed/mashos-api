-- B4 / M4 + B5 preview persistence FILE-ONLY CANDIDATE. No production application or route activation.
-- PCE-3/6/8: first save + immutable consumption; visibility; physical delete.
-- The backend supplies an authenticated owner, NOT a client-provided user_id.
-- B5/B6 still own source/preview admission and current format/visual eligibility.
-- Internal RPCs only: no PUBLIC/client EXECUTE and no service direct DML grants.
-- Tier owner is the existing public.profiles(id, subscription_tier), read afresh
-- under a row lock. Non-default subscription table/column deployments require
-- explicit reconciliation before application; runtime env overrides are not SQL.
-- Server time is sampled after lock waits. Call one RPC per short transaction.
-- This file does not change old public.pieces, billing state or migration history.
DO $piece_atomic$
DECLARE
    object_name text;
    signature text;
    acl_entry record;
BEGIN
    IF pg_catalog.to_regclass('public.pieces_v2_staging') IS NULL
       OR pg_catalog.to_regclass('public.profiles') IS NULL THEN
        RAISE EXCEPTION 'PIECE_B4_PRECONDITION';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute
        WHERE attrelid='public.profiles'::regclass AND attname='id'
          AND atttypid='uuid'::regtype AND NOT attisdropped)
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute
        WHERE attrelid='public.profiles'::regclass AND attname='subscription_tier'
          AND atttypid='text'::regtype AND NOT attisdropped) THEN
        RAISE EXCEPTION 'PIECE_B4_PRECONDITION';
    END IF;
    FOREACH object_name IN ARRAY ARRAY['piece_records','piece_quota_month_locks',
        'piece_quota_consumptions','piece_record_metrics','piece_record_reads',
        'piece_record_resonances','piece_export_receipts','piece_delete_receipts'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_class
            WHERE oid=pg_catalog.to_regclass('public.' || object_name)
              AND relkind='r' AND relrowsecurity AND relforcerowsecurity) THEN
            RAISE EXCEPTION 'PIECE_B4_PRECONDITION';
        END IF;
    END LOOP;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        WHERE n.nspname='public' AND p.proname IN
            ('piece_save_v2','piece_set_visibility_v2','piece_delete_v2',
             'piece_issue_preview_v2','piece_cancel_preview_v2')) THEN
        RAISE EXCEPTION 'PIECE_B4_TARGET_EXISTS';
    END IF;

    -- B5 persistence extension of the still-unapplied M4 candidate. These two
    -- metadata columns describe preview retries; neither replaces save identity.
    -- No new table, client grant, source reader, safety verdict or API is added.
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_attribute
        WHERE attrelid='public.piece_records'::regclass AND NOT attisdropped
          AND attname IN ('preview_request_hash','preview_eligible_formats')) THEN
        RAISE EXCEPTION 'PIECE_B5_TARGET_EXISTS';
    END IF;
    ALTER TABLE public.piece_records
        ADD COLUMN preview_request_hash text,
        ADD COLUMN preview_eligible_formats jsonb,
        ADD CONSTRAINT piece_records_preview_request_shape CHECK ((
            (preview_request_hash IS NULL AND preview_eligible_formats IS NULL)
            OR (preview_request_hash ~ '^[0-9a-f]{64}$'
                AND jsonb_typeof(preview_eligible_formats)='array'
                AND jsonb_array_length(preview_eligible_formats) BETWEEN 1 AND 3
                AND preview_eligible_formats <@ '["short_essay","quote","declaration"]'::jsonb
                AND preview_eligible_formats ? format_type)
        ) IS TRUE);

    CREATE FUNCTION public.piece_issue_preview_v2(
        p_owner_user_id uuid, p_idempotency_key_hash text, p_request_hash text,
        p_record jsonb, p_ttl_seconds integer
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $issue$
    DECLARE
        r public.piece_records%ROWTYPE;
        preview_id uuid;
        replayed boolean := false;
        at_time timestamptz;
        fields text[] := ARRAY['source_lineage','format_type','content_payload',
            'content_payload_hash','piece_text','piece_text_hash','safety_state',
            'visual_recipe','visual_recipe_hash','renderer_version','eligible_formats'];
    BEGIN
        IF p_owner_user_id IS NULL OR p_owner_user_id='00000000-0000-0000-0000-000000000000'::uuid THEN
            RAISE EXCEPTION 'PIECE_AUTH_REQUIRED';
        END IF;
        IF p_idempotency_key_hash IS NULL OR p_idempotency_key_hash !~ '^[0-9a-f]{64}$'
           OR p_request_hash IS NULL OR p_request_hash !~ '^[0-9a-f]{64}$'
           OR p_ttl_seconds IS NULL OR p_ttl_seconds<1 THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF (jsonb_typeof(p_record)='object' AND p_record ?& fields
            AND p_record-fields='{}'::jsonb
            AND jsonb_typeof(p_record->'eligible_formats')='array') IS NOT TRUE THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF (jsonb_array_length(p_record->'eligible_formats') BETWEEN 1 AND 3
            AND p_record->'eligible_formats' <@ '["short_essay","quote","declaration"]'::jsonb
            AND (p_record->'eligible_formats') ? (p_record->>'format_type')
            AND (SELECT count(DISTINCT value) FROM jsonb_array_elements(p_record->'eligible_formats'))
                =jsonb_array_length(p_record->'eligible_formats')
            AND p_record#>>'{source_lineage,source_input,source_owner_user_id}'=p_owner_user_id::text
        ) IS NOT TRUE THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        -- Stable opaque logical ID permits the existing delete receipt to stop
        -- resurrection, without a new receipt/ledger table. A hash collision
        -- can only serialize or reject; it can never adopt another owner's row.
        preview_id := substr(encode(sha256(convert_to(
            'piece.preview.v2:'||p_owner_user_id::text||':'||p_idempotency_key_hash,'UTF8')),'hex'),1,32)::uuid;
        PERFORM pg_advisory_xact_lock(hashtextextended('piece.preview.v2:'||preview_id::text,0));
        SELECT * INTO r FROM public.piece_records WHERE id=preview_id FOR UPDATE;
        IF FOUND THEN
            IF r.owner_user_id<>p_owner_user_id OR r.preview_request_hash IS DISTINCT FROM p_request_hash
               OR r.lifecycle_status<>'preview_draft' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            IF r.expires_at IS NULL OR r.expires_at<=clock_timestamp() THEN
                RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED';
            END IF;
            replayed := true;
        ELSE
            -- SELECT is deliberately after the row-lock wait: a concurrent
            -- delete may have committed its retained receipt while we waited.
            IF EXISTS (SELECT 1 FROM public.piece_delete_receipts WHERE piece_id=preview_id) THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            at_time := clock_timestamp();
            INSERT INTO public.piece_records(id,owner_user_id,source_input_id,source_input_version,
                source_input_bundle_commitment,source_lineage,expires_at,format_type,
                content_payload,content_payload_hash,piece_text,piece_text_hash,safety_state,
                visual_recipe,visual_recipe_hash,renderer_version,preview_request_hash,
                preview_eligible_formats,created_at,updated_at)
            VALUES(preview_id,p_owner_user_id,
                p_record#>>'{source_lineage,source_input,source_input_id}',
                p_record#>>'{source_lineage,source_input,source_input_version}',
                p_record#>>'{source_lineage,source_input,source_input_bundle_commitment}',
                p_record->'source_lineage',at_time+make_interval(secs=>p_ttl_seconds),
                p_record->>'format_type',p_record->'content_payload',p_record->>'content_payload_hash',
                p_record->>'piece_text',p_record->>'piece_text_hash',p_record->>'safety_state',
                p_record->'visual_recipe',p_record->>'visual_recipe_hash',p_record->>'renderer_version',
                p_request_hash,p_record->'eligible_formats',at_time,at_time) RETURNING * INTO r;
        END IF;
        -- Return the persisted first candidate, not the caller's possibly
        -- recomputed body. Replay never extends expiry or consumes quota.
        RETURN jsonb_build_object('preview_id',r.id,'preview_revision',r.preview_revision,
            'row_version',r.row_version,'expires_at',r.expires_at,'visibility_scope',r.visibility_scope,
            'format_type',r.format_type,'eligible_formats',r.preview_eligible_formats,
            'content_payload',r.content_payload,'content_payload_hash',r.content_payload_hash,
            'piece_text',r.piece_text,'piece_text_hash',r.piece_text_hash,'safety_state',r.safety_state,
            'visual_recipe',r.visual_recipe,'visual_recipe_hash',r.visual_recipe_hash,
            'renderer_version',r.renderer_version,'idempotency_replayed',replayed);
    EXCEPTION WHEN unique_violation THEN
        RAISE EXCEPTION 'PIECE_CONFLICT';
    WHEN check_violation OR not_null_violation OR invalid_text_representation THEN
        RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
    END;
    $issue$;

    -- B5 server-only final source fence. The existing five-argument storage
    -- primitive remains unchanged; this seven-argument overload adds current
    -- admission and holds the same B6 original/profile/thread/context locks
    -- through issuance. No defaults: incomplete expectations cannot select it.
    CREATE FUNCTION public.piece_issue_preview_v2(
        p_owner_user_id uuid, p_idempotency_key_hash text, p_request_hash text,
        p_record jsonb, p_ttl_seconds integer,
        p_expected_subscription_tier text, p_expected_source_state jsonb
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $issue_fenced$
    DECLARE
        r public.piece_records%ROWTYPE;
        preview_id uuid;
        tier text;
        at_time timestamptz;
        fields text[] := ARRAY['source_lineage','format_type','content_payload',
            'content_payload_hash','piece_text','piece_text_hash','safety_state',
            'visual_recipe','visual_recipe_hash','renderer_version','eligible_formats'];
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
        IF p_idempotency_key_hash IS NULL OR p_idempotency_key_hash !~ '^[0-9a-f]{64}$'
           OR p_request_hash IS NULL OR p_request_hash !~ '^[0-9a-f]{64}$'
           OR p_ttl_seconds IS NULL OR p_ttl_seconds<1 THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF (jsonb_typeof(p_record)='object' AND p_record ?& fields
            AND p_record-fields='{}'::jsonb
            AND jsonb_typeof(p_record->'eligible_formats')='array') IS NOT TRUE THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF (jsonb_array_length(p_record->'eligible_formats') BETWEEN 1 AND 3
            AND p_record->'eligible_formats' <@ '["short_essay","quote","declaration"]'::jsonb
            AND (p_record->'eligible_formats') ? (p_record->>'format_type')
            AND (SELECT count(DISTINCT value) FROM jsonb_array_elements(p_record->'eligible_formats'))
                =jsonb_array_length(p_record->'eligible_formats')
            AND p_record#>>'{source_lineage,source_input,source_owner_user_id}'=p_owner_user_id::text
        ) IS NOT TRUE THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF p_expected_subscription_tier IS NULL
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
        IF p_record->'source_lineage' IS DISTINCT FROM p_expected_source_state->'lineage' THEN
            RAISE EXCEPTION 'PIECE_CONFLICT';
        END IF;
        -- Match the existing issue/save/delete order: preview identity and row
        -- first, then original -> profile -> thread -> sorted consumed context.
        -- Re-entering the storage primitive below cannot wait on these locks.
        preview_id := substr(encode(sha256(convert_to(
            'piece.preview.v2:'||p_owner_user_id::text||':'||p_idempotency_key_hash,'UTF8')),'hex'),1,32)::uuid;
        PERFORM pg_advisory_xact_lock(hashtextextended('piece.preview.v2:'||preview_id::text,0));
        SELECT * INTO r FROM public.piece_records WHERE id=preview_id FOR UPDATE;
        IF FOUND THEN
            IF r.owner_user_id<>p_owner_user_id OR r.preview_request_hash IS DISTINCT FROM p_request_hash
               OR r.lifecycle_status<>'preview_draft'
               OR r.source_lineage IS DISTINCT FROM p_expected_source_state->'lineage' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
        ELSE
            r.source_lineage := p_record->'source_lineage';
            r.source_input_id := p_record#>>'{source_lineage,source_input,source_input_id}';
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
        RETURN public.piece_issue_preview_v2(p_owner_user_id,p_idempotency_key_hash,
            p_request_hash,p_record,p_ttl_seconds);
    END;
    $issue_fenced$;

    CREATE FUNCTION public.piece_cancel_preview_v2(
        p_owner_user_id uuid, p_preview_id uuid, p_expected_preview_revision bigint
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $cancel$
    DECLARE r public.piece_records%ROWTYPE;
    BEGIN
        IF p_owner_user_id IS NULL THEN RAISE EXCEPTION 'PIECE_AUTH_REQUIRED'; END IF;
        IF p_preview_id IS NULL OR p_expected_preview_revision IS NULL OR p_expected_preview_revision<1 THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        SELECT * INTO r FROM public.piece_records
            WHERE id=p_preview_id AND owner_user_id=p_owner_user_id FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
        IF r.preview_revision<>p_expected_preview_revision THEN RAISE EXCEPTION 'PIECE_PREVIEW_STALE'; END IF;
        IF r.lifecycle_status='cancelled' THEN
            RETURN jsonb_build_object('preview_id',r.id,'preview_revision',r.preview_revision,
                'row_version',r.row_version,'lifecycle_status','cancelled','idempotency_replayed',true);
        END IF;
        IF r.lifecycle_status<>'preview_draft' THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
        IF r.expires_at IS NULL OR r.expires_at<=clock_timestamp() THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED';
        END IF;
        UPDATE public.piece_records SET lifecycle_status='cancelled',row_version=row_version+1,
            updated_at=clock_timestamp() WHERE id=r.id RETURNING * INTO r;
        RETURN jsonb_build_object('preview_id',r.id,'preview_revision',r.preview_revision,
            'row_version',r.row_version,'lifecycle_status','cancelled','idempotency_replayed',false);
    END;
    $cancel$;

    CREATE FUNCTION public.piece_save_v2(
        p_owner_user_id uuid, p_preview_id uuid, p_expected_preview_revision bigint,
        p_piece_text_hash text, p_content_payload_hash text, p_visual_recipe_hash text,
        p_idempotency_key_hash text, p_visibility_scope text DEFAULT 'private',
        p_expected_subscription_tier text DEFAULT NULL,
        p_expected_source_state jsonb DEFAULT NULL,
        p_replay_only boolean DEFAULT false
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $save$
    DECLARE
        r public.piece_records%ROWTYPE;
        q public.piece_quota_consumptions%ROWTYPE;
        tier text;
        save_limit integer;
        used_count bigint;
        at_time timestamptz;
        month_value text;
        visibility text := coalesce(p_visibility_scope, 'private');
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
        IF p_owner_user_id IS NULL THEN RAISE EXCEPTION 'PIECE_AUTH_REQUIRED'; END IF;
        IF p_preview_id IS NULL OR p_expected_preview_revision IS NULL
           OR p_expected_preview_revision < 1 OR visibility NOT IN ('private','public')
           OR p_piece_text_hash IS NULL OR p_piece_text_hash !~ '^[0-9a-f]{64}$'
           OR p_content_payload_hash IS NULL OR p_content_payload_hash !~ '^[0-9a-f]{64}$'
           OR p_visual_recipe_hash IS NULL OR p_visual_recipe_hash !~ '^[0-9a-f]{64}$'
           OR p_idempotency_key_hash IS NULL OR p_idempotency_key_hash !~ '^[0-9a-f]{64}$' THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF p_expected_subscription_tier IS NOT NULL
           AND p_expected_subscription_tier NOT IN ('free','plus','premium') THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        IF p_replay_only IS NULL THEN RAISE EXCEPTION 'PIECE_REQUEST_INVALID'; END IF;
        IF p_expected_source_state IS NOT NULL AND (
            jsonb_typeof(p_expected_source_state)='object'
            AND p_expected_source_state ?& ARRAY['original','thread_id','thread_revision','lineage']
            AND p_expected_source_state-ARRAY['original','thread_id','thread_revision','lineage']='{}'::jsonb
            AND jsonb_typeof(p_expected_source_state->'original')='object'
            AND jsonb_typeof(p_expected_source_state->'lineage')='object'
            AND jsonb_typeof(p_expected_source_state->'thread_id')='string'
            AND jsonb_typeof(p_expected_source_state->'thread_revision')='number'
            AND (p_expected_source_state->>'thread_revision') ~ '^[1-9][0-9]*$'
            AND p_expected_subscription_tier IS NOT NULL
        ) IS NOT TRUE THEN RAISE EXCEPTION 'PIECE_REQUEST_INVALID'; END IF;
        SELECT * INTO r FROM public.piece_records
            WHERE id=p_preview_id AND owner_user_id=p_owner_user_id FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
        IF r.preview_revision <> p_expected_preview_revision THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_STALE';
        END IF;
        IF r.piece_text_hash <> p_piece_text_hash
           OR r.content_payload_hash <> p_content_payload_hash
           OR r.visual_recipe_hash <> p_visual_recipe_hash THEN
            RAISE EXCEPTION 'PIECE_HASH_MISMATCH';
        END IF;
        SELECT * INTO q FROM public.piece_quota_consumptions
            WHERE owner_user_id=p_owner_user_id AND save_idempotency_key_hash=p_idempotency_key_hash;
        IF FOUND THEN
            IF q.piece_id <> r.id OR r.lifecycle_status <> 'saved'
               OR r.save_idempotency_key_hash IS DISTINCT FROM p_idempotency_key_hash THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            -- Replay never restores an older visibility or resurrects a deleted row.
            RETURN jsonb_build_object('piece_id',r.id,'consumption_id',q.consumption_id,
                'lifecycle_status',r.lifecycle_status,'visibility_scope',r.visibility_scope,
                'row_version',r.row_version,'saved_at',r.saved_at,'idempotency_replayed',true);
        END IF;
        IF r.lifecycle_status <> 'preview_draft' THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
        IF p_replay_only THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
        IF r.expires_at IS NULL OR r.expires_at <= clock_timestamp() THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED';
        END IF;
        -- Optional backend pre-save expectation, NEVER an entitlement grant.
        -- B5/B6 must derive it from current server state, not a request field.
        -- NULL preserves the low-level B4 caller; it is not B6 admission.
        -- Current DB tier remains authoritative for both the comparison and quota.
        -- Keep the shared source owner's lock order: original -> profile ->
        -- thread. These are reads only, bound to the authenticated server
        -- snapshot. NULL retains B4 compatibility, never B6 admission.
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
        save_limit := CASE tier WHEN 'free' THEN 5 WHEN 'plus' THEN 30 ELSE NULL END;
        LOOP
            at_time := clock_timestamp();
            month_value := to_char(at_time AT TIME ZONE 'Asia/Tokyo','YYYY-MM');
            INSERT INTO public.piece_quota_month_locks(owner_user_id,month_key)
                VALUES (p_owner_user_id,month_value) ON CONFLICT DO NOTHING;
            PERFORM 1 FROM public.piece_quota_month_locks
                WHERE owner_user_id=p_owner_user_id AND month_key=month_value FOR UPDATE;
            at_time := clock_timestamp();
            EXIT WHEN month_value=to_char(at_time AT TIME ZONE 'Asia/Tokyo','YYYY-MM');
        END LOOP;
        IF r.expires_at <= at_time THEN RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED'; END IF;
        IF p_expected_source_state IS NOT NULL THEN
            IF public.emlis_parent_visible(source_created,tier,at_time) IS NOT TRUE THEN
                RAISE EXCEPTION 'PIECE_NOT_FOUND';
            END IF;
        END IF;
        IF q3_context THEN
            -- Q3's read owner uses statement time. Explicitly check consumed
            -- rows with the post-wait clock so a quota/row wait cannot keep
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
        -- Another preview may have consumed this key while the month lock waited.
        IF EXISTS (SELECT 1 FROM public.piece_quota_consumptions
            WHERE owner_user_id=p_owner_user_id AND save_idempotency_key_hash=p_idempotency_key_hash) THEN
            RAISE EXCEPTION 'PIECE_CONFLICT';
        END IF;
        SELECT count(*) INTO used_count FROM public.piece_quota_consumptions
            WHERE owner_user_id=p_owner_user_id AND month_key=month_value;
        IF save_limit IS NOT NULL AND used_count >= save_limit THEN
            RAISE EXCEPTION 'PIECE_QUOTA_EXHAUSTED';
        END IF;
        UPDATE public.piece_records SET lifecycle_status='saved',visibility_scope=visibility,
            saved_at=at_time,expires_at=NULL,save_idempotency_key_hash=p_idempotency_key_hash,
            row_version=row_version+1,updated_at=at_time WHERE id=r.id RETURNING * INTO r;
        INSERT INTO public.piece_quota_consumptions(owner_user_id,piece_id,month_key,
            subscription_tier_at_consumption,consumed_at,save_idempotency_key_hash)
            VALUES (p_owner_user_id,r.id,month_value,tier,at_time,p_idempotency_key_hash)
            RETURNING * INTO q;
        RETURN jsonb_build_object('piece_id',r.id,'consumption_id',q.consumption_id,
            'lifecycle_status',r.lifecycle_status,'visibility_scope',r.visibility_scope,
            'row_version',r.row_version,'saved_at',r.saved_at,'idempotency_replayed',false);
    EXCEPTION WHEN unique_violation THEN
        -- Also covers simultaneous reuse across a calendar-month boundary.
        -- PL/pgSQL rolls back all mutations in this function before raising.
        RAISE EXCEPTION 'PIECE_CONFLICT';
    END;
    $save$;

    CREATE FUNCTION public.piece_set_visibility_v2(
        p_owner_user_id uuid, p_piece_id uuid, p_expected_row_version bigint,
        p_visibility_scope text
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $visibility$
    DECLARE r public.piece_records%ROWTYPE;
    BEGIN
        IF p_owner_user_id IS NULL THEN RAISE EXCEPTION 'PIECE_AUTH_REQUIRED'; END IF;
        IF p_piece_id IS NULL OR p_expected_row_version IS NULL OR p_expected_row_version<1
           OR p_visibility_scope IS NULL OR p_visibility_scope NOT IN ('private','public') THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        SELECT * INTO r FROM public.piece_records
            WHERE id=p_piece_id AND owner_user_id=p_owner_user_id AND lifecycle_status='saved' FOR UPDATE;
        IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
        IF r.row_version <> p_expected_row_version THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
        IF r.visibility_scope=p_visibility_scope THEN
            RETURN jsonb_build_object('piece_id',r.id,'visibility_scope',r.visibility_scope,'row_version',r.row_version);
        END IF;
        UPDATE public.piece_records SET visibility_scope=p_visibility_scope,
            row_version=row_version+1,updated_at=clock_timestamp() WHERE id=r.id RETURNING * INTO r;
        RETURN jsonb_build_object('piece_id',r.id,'visibility_scope',r.visibility_scope,'row_version',r.row_version);
    END;
    $visibility$;

    CREATE FUNCTION public.piece_delete_v2(
        p_owner_user_id uuid, p_piece_id uuid, p_expected_row_version bigint,
        p_idempotency_key_hash text
    ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $delete$
    DECLARE
        r public.piece_records%ROWTYPE;
        receipt public.piece_delete_receipts%ROWTYPE;
    BEGIN
        IF p_owner_user_id IS NULL THEN RAISE EXCEPTION 'PIECE_AUTH_REQUIRED'; END IF;
        IF p_piece_id IS NULL OR p_expected_row_version IS NULL OR p_expected_row_version<1
           OR p_idempotency_key_hash IS NULL OR p_idempotency_key_hash !~ '^[0-9a-f]{64}$' THEN
            RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
        END IF;
        SELECT * INTO r FROM public.piece_records
            WHERE id=p_piece_id AND owner_user_id=p_owner_user_id FOR UPDATE;
        -- Recheck receipt AFTER waiting on the row: a concurrent delete may have
        -- committed the receipt and removed the record while this call waited.
        SELECT * INTO receipt FROM public.piece_delete_receipts
            WHERE owner_user_id=p_owner_user_id AND idempotency_key_hash=p_idempotency_key_hash;
        IF FOUND THEN
            IF receipt.piece_id<>p_piece_id OR receipt.outcome<>'succeeded' THEN
                RAISE EXCEPTION 'PIECE_CONFLICT';
            END IF;
            RETURN jsonb_build_object('piece_id',receipt.piece_id,'receipt_id',receipt.receipt_id,
                'outcome',receipt.outcome,'idempotency_replayed',true);
        END IF;
        IF r.id IS NULL OR r.lifecycle_status<>'saved' THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
        IF r.row_version<>p_expected_row_version THEN RAISE EXCEPTION 'PIECE_CONFLICT'; END IF;
        INSERT INTO public.piece_delete_receipts(owner_user_id,piece_id,idempotency_key_hash,outcome)
            VALUES(p_owner_user_id,r.id,p_idempotency_key_hash,'succeeded') RETURNING * INTO receipt;
        -- FK cascades purge metrics/reads/resonances; quota and receipts have no FK.
        DELETE FROM public.piece_records WHERE id=r.id;
        RETURN jsonb_build_object('piece_id',receipt.piece_id,'receipt_id',receipt.receipt_id,
            'outcome',receipt.outcome,'idempotency_replayed',false);
    EXCEPTION WHEN unique_violation THEN
        RAISE EXCEPTION 'PIECE_CONFLICT';
    END;
    $delete$;

    FOREACH signature IN ARRAY ARRAY[
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text,text,jsonb,boolean)',
        'public.piece_set_visibility_v2(uuid,uuid,bigint,text)',
        'public.piece_delete_v2(uuid,uuid,bigint,text)',
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer)',
        'public.piece_issue_preview_v2(uuid,text,text,jsonb,integer,text,jsonb)',
        'public.piece_cancel_preview_v2(uuid,uuid,bigint)'] LOOP
        EXECUTE 'REVOKE ALL ON FUNCTION ' || signature || ' FROM PUBLIC, anon, authenticated, service_role';
        -- Remove inherited function default ACLs too, without changing defaults.
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
    END LOOP;
END;
$piece_atomic$;
