-- Piece quota display, SOURCE-ONLY CANDIDATE; live application not authorized.
-- Existing 001-004 remain byte-for-byte unchanged and already applied live.
-- No table/row/policy changes or direct table grants. The backend passes only
-- the authenticated owner; clients cannot execute this function directly.
DO $piece_quota_read$
DECLARE
    acl_entry record;
BEGIN
    IF pg_catalog.to_regclass('public.piece_quota_consumptions') IS NULL
       OR pg_catalog.to_regclass('public.profiles') IS NULL
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='service_role')
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles
                      WHERE rolname=current_user AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'PIECE_QUOTA_READ_PRECONDITION';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        WHERE n.nspname='public' AND p.proname='piece_read_quota_v2') THEN
        RAISE EXCEPTION 'PIECE_QUOTA_READ_TARGET_EXISTS';
    END IF;

    CREATE FUNCTION public.piece_read_quota_v2(p_owner_user_id uuid)
    RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
    SET search_path=pg_catalog SET row_security=off AS $read_quota$
    DECLARE
        at_time timestamptz := statement_timestamp();
        at_month text;
        tier text;
        used bigint;
    BEGIN
        IF p_owner_user_id IS NULL
           OR p_owner_user_id='00000000-0000-0000-0000-000000000000'::uuid THEN
            RAISE EXCEPTION 'PIECE_AUTH_REQUIRED';
        END IF;
        at_month := to_char(at_time AT TIME ZONE 'Asia/Tokyo','YYYY-MM');
        SELECT subscription_tier INTO tier FROM public.profiles WHERE id=p_owner_user_id;
        tier := CASE WHEN tier IN ('free','plus','premium') THEN tier ELSE 'free' END;
        SELECT count(*) INTO used FROM public.piece_quota_consumptions
            WHERE owner_user_id=p_owner_user_id AND month_key=at_month;
        RETURN jsonb_build_object('subscription_tier',tier,'saved_count',used,'server_now',at_time);
    END;
    $read_quota$;

    REVOKE ALL ON FUNCTION public.piece_read_quota_v2(uuid)
        FROM PUBLIC, anon, authenticated, service_role;
    -- Match M4: remove inherited default function ACLs, without changing the
    -- defaults or granting service/client access to either underlying table.
    FOR acl_entry IN SELECT DISTINCT roles.rolname
        FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,
            pg_catalog.acldefault('f',p.proowner))) a
        JOIN pg_catalog.pg_roles roles ON roles.oid=a.grantee
        WHERE p.oid='public.piece_read_quota_v2(uuid)'::regprocedure AND a.grantee<>p.proowner
    LOOP
        EXECUTE format('REVOKE ALL ON FUNCTION public.piece_read_quota_v2(uuid) FROM %I',acl_entry.rolname);
    END LOOP;
    GRANT EXECUTE ON FUNCTION public.piece_read_quota_v2(uuid) TO service_role;
END;
$piece_quota_read$;
