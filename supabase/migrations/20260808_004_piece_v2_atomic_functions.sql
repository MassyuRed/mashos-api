-- B4 / M4 FILE-ONLY CANDIDATE. No production application or route activation.
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
            ('piece_save_v2','piece_set_visibility_v2','piece_delete_v2')) THEN
        RAISE EXCEPTION 'PIECE_B4_TARGET_EXISTS';
    END IF;

    CREATE FUNCTION public.piece_save_v2(
        p_owner_user_id uuid, p_preview_id uuid, p_expected_preview_revision bigint,
        p_piece_text_hash text, p_content_payload_hash text, p_visual_recipe_hash text,
        p_idempotency_key_hash text, p_visibility_scope text DEFAULT 'private'
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
        IF r.expires_at IS NULL OR r.expires_at <= clock_timestamp() THEN
            RAISE EXCEPTION 'PIECE_PREVIEW_EXPIRED';
        END IF;
        -- No caller tier/limit parameter, no process-local entitlement cache.
        SELECT subscription_tier INTO tier FROM public.profiles
            WHERE id=p_owner_user_id FOR SHARE;
        tier := CASE WHEN tier IN ('free','plus','premium') THEN tier ELSE 'free' END;
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
        'public.piece_save_v2(uuid,uuid,bigint,text,text,text,text,text)',
        'public.piece_set_visibility_v2(uuid,uuid,bigint,text)',
        'public.piece_delete_v2(uuid,uuid,bigint,text)'] LOOP
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
