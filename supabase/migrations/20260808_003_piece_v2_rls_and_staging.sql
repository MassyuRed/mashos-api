-- B3 FILE-ONLY candidate. Path fixed by PCE-8; no production application.
-- PCE-3 visibility/access + PCE-6 data contract. B2/M2 must exist first.
-- Only backend SELECT is enabled here. Service credentials are NOT a viewer
-- decision: piece_v2_access and the current viewer relation remain mandatory.
-- No base DML, RPC, quota, notification, public.pieces replacement or live data.
-- B4 owns atomic write grants/functions; B5/B7/B12 own authenticated API wiring.
-- PRODUCTION_APPLICATION_REQUIRES_SEPARATE_MASH_APPROVAL
DO $piece_access$
DECLARE
    target text;
    obj oid;
    actor oid := (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = current_user);
    acl_entry record;
    tables text[] := ARRAY['piece_records','piece_quota_month_locks',
        'piece_quota_consumptions','piece_record_metrics','piece_record_reads',
        'piece_record_resonances','piece_export_receipts','piece_delete_receipts'];
BEGIN
    IF current_setting('server_version_num')::integer < 150000
       OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
        RAISE EXCEPTION 'PIECE_B3_PRECONDITION: PostgreSQL 15 and service role required';
    END IF;
    IF pg_catalog.to_regclass('public.pieces_v2_staging') IS NOT NULL THEN
        RAISE EXCEPTION 'PIECE_B3_TARGET_EXISTS';
    END IF;
    FOREACH target IN ARRAY tables LOOP
        obj := pg_catalog.to_regclass('public.' || target);
        IF obj IS NULL OR NOT EXISTS (
            SELECT 1 FROM pg_catalog.pg_class
             WHERE oid = obj AND relkind = 'r' AND relowner = actor
               AND relrowsecurity AND relforcerowsecurity
        ) OR EXISTS (SELECT 1 FROM pg_catalog.pg_policy WHERE polrelid = obj) THEN
            RAISE EXCEPTION 'PIECE_B3_PRECONDITION: unchanged M2 table owner and RLS required';
        END IF;
        -- M2 is deny-all. Do not silently adopt unexpected grants or policies.
        IF EXISTS (
            SELECT 1 FROM pg_catalog.pg_class c
            CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,
                pg_catalog.acldefault('r', c.relowner))) a
            WHERE c.oid = obj AND a.grantee <> c.relowner
        ) OR EXISTS (
            SELECT 1 FROM pg_catalog.pg_attribute
             WHERE attrelid = obj AND attnum > 0 AND NOT attisdropped
               AND cardinality(attacl) > 0
        ) THEN
            RAISE EXCEPTION 'PIECE_B3_PRECONDITION: unchanged M2 privileges required';
        END IF;
    END LOOP;

    -- This also works with a NOBYPASSRLS service role. The backend applies the
    -- owner/current-viewer decision. anon/authenticated still have no access.
    CREATE POLICY piece_records_service_select ON public.piece_records
        FOR SELECT TO service_role USING (true);
    GRANT SELECT ON public.piece_records TO service_role;

    -- A public-candidate projection, NOT an unauthenticated/public feed API.
    -- No raw source, lineage, internal safety, quota or receipt is projected.
    CREATE VIEW public.pieces_v2_staging
    WITH (security_invoker = true, security_barrier = true) AS
    SELECT id AS piece_id, public_id, owner_user_id, format_type,
           piece_text, piece_text_hash, visual_recipe, visual_recipe_hash,
           saved_at, row_version
      FROM public.piece_records
     WHERE lifecycle_status = 'saved' AND visibility_scope = 'public';

    REVOKE ALL ON public.pieces_v2_staging FROM PUBLIC;
    FOR acl_entry IN
        SELECT DISTINCT r.rolname
          FROM pg_catalog.pg_class c
          CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,
              pg_catalog.acldefault('r', c.relowner))) a
          JOIN pg_catalog.pg_roles r ON r.oid = a.grantee
         WHERE c.oid = 'public.pieces_v2_staging'::regclass
           AND a.grantee <> c.relowner
    LOOP
        EXECUTE format('REVOKE ALL ON public.pieces_v2_staging FROM %I', acl_entry.rolname);
    END LOOP;
    GRANT SELECT ON public.pieces_v2_staging TO service_role;
END
$piece_access$;
