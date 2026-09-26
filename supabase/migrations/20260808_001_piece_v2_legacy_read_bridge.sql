-- migration_id: 20260808_001_piece_v2_legacy_read_bridge
-- expected_pce0_catalog_sha256: 2f51e5e6e4207a186aaacbeb355c07ade3b4f777960f3f46d1dbea9f8f9d810e
-- M1 only. The hash identifies the historical PCE-0 packet, not a live DB claim.
-- One atomic statement: reject the consumed catalog shape before creating a view.
-- No source-row write; no change to public.pieces, its owner, ACL or definition.
-- PRODUCTION_APPLICATION_REQUIRES_SEPARATE_MASH_APPROVAL
DO $piece_bridge$
DECLARE
    base_oid oid := pg_catalog.to_regclass('public.mymodel_reflections');
    old_oid oid := pg_catalog.to_regclass('public.pieces');
    bridge_oid oid := pg_catalog.to_regclass('public.mymodel_reflections_read');
    expected_names text[] := ARRAY['id','public_id','owner_user_id','source_type','status','is_active','question_id','q_key','topic_key','category','question','answer','content_json','source_snapshot_id','source_hash','source_refs','locked','lock_note','created_at','updated_at','published_at'];
    expected_types text[] := ARRAY['uuid','text','uuid','text','text','bool','int4','text','text','text','text','text','jsonb','uuid','text','jsonb','bool','text','timestamptz','timestamptz','timestamptz'];
    names text[];
    types text[];
    expected_definition text;
    relation_oid oid;
    relation_owner oid;
    acl_row record;
BEGIN
    IF base_oid IS NULL OR old_oid IS NULL OR
       (SELECT relkind FROM pg_catalog.pg_class WHERE oid=base_oid) <> 'r' OR
       (SELECT relkind FROM pg_catalog.pg_class WHERE oid=old_oid) <> 'v' THEN
        RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: source relation kind';
    END IF;
    SELECT relowner INTO relation_owner FROM pg_catalog.pg_class WHERE oid=old_oid;
    IF relation_owner <> (SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user) THEN
        RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: migration owner';
    END IF;
    -- These locks prevent concurrent schema edits until this statement/transaction ends.
    LOCK TABLE public.mymodel_reflections IN ACCESS SHARE MODE;
    LOCK TABLE public.pieces IN ACCESS SHARE MODE;
    FOREACH relation_oid IN ARRAY ARRAY[base_oid, old_oid] LOOP
        SELECT array_agg(a.attname::text ORDER BY a.attnum),
               array_agg(t.typname::text ORDER BY a.attnum)
          INTO names, types
          FROM pg_catalog.pg_attribute a
          JOIN pg_catalog.pg_type t ON t.oid=a.atttypid
         WHERE a.attrelid=relation_oid AND a.attnum>0 AND NOT a.attisdropped;
        IF names IS DISTINCT FROM expected_names OR types IS DISTINCT FROM expected_types THEN
            RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: projection columns or types';
        END IF;
    END LOOP;
    SELECT 'select' || string_agg(name, ',' ORDER BY ord)
           || 'frommymodel_reflections;'
      INTO expected_definition FROM unnest(expected_names) WITH ORDINALITY AS c(name,ord);
    IF NOT ('security_invoker=true'=ANY(COALESCE(
        (SELECT reloptions FROM pg_catalog.pg_class WHERE oid=old_oid), ARRAY[]::text[]))) OR
       lower(regexp_replace(replace(replace(pg_catalog.pg_get_viewdef(old_oid, false),
           'public.', ''), 'mymodel_reflections.', ''), '\s+', '', 'g')) IS DISTINCT FROM expected_definition THEN
        RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: legacy view semantics';
    END IF;
    -- Column-level ACLs survive table-level REVOKE and must not be silently inherited.
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_attribute
        WHERE attrelid IN (old_oid, bridge_oid) AND attnum>0 AND NOT attisdropped
          AND cardinality(attacl)>0) THEN
        RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: column grants';
    END IF;
    -- PCE-0 permits only the relation owner and service_role to SELECT this read view.
    FOR acl_row IN
        SELECT x.grantee, r.rolname
          FROM pg_catalog.pg_class c
          CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(c.relacl,
              pg_catalog.acldefault('r',c.relowner))) x
          LEFT JOIN pg_catalog.pg_roles r ON r.oid=x.grantee
         WHERE c.oid=old_oid AND x.privilege_type='SELECT'
    LOOP
        IF acl_row.grantee <> relation_owner AND
           (acl_row.grantee=0 OR acl_row.rolname IS DISTINCT FROM 'service_role') THEN
            RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: legacy read grants';
        END IF;
    END LOOP;
    IF bridge_oid IS NOT NULL THEN
        IF (SELECT relkind FROM pg_catalog.pg_class WHERE oid=bridge_oid) <> 'v' OR
           (SELECT relowner FROM pg_catalog.pg_class WHERE oid=bridge_oid) <> relation_owner THEN
            RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: existing bridge identity';
        END IF;
        IF NOT ('security_invoker=true'=ANY(COALESCE(
            (SELECT reloptions FROM pg_catalog.pg_class WHERE oid=bridge_oid), ARRAY[]::text[]))) OR
           lower(regexp_replace(replace(replace(pg_catalog.pg_get_viewdef(bridge_oid, false),
               'public.', ''), 'mymodel_reflections.', ''), '\s+', '', 'g')) IS DISTINCT FROM expected_definition THEN
            RAISE EXCEPTION 'PIECE_M1_CATALOG_DRIFT: existing bridge semantics';
        END IF;
    END IF;

    CREATE OR REPLACE VIEW public.mymodel_reflections_read
    WITH (security_invoker = true) AS
    SELECT id, public_id, owner_user_id, source_type, status, is_active, question_id, q_key, topic_key, category, question, answer, content_json, source_snapshot_id, source_hash, source_refs, locked, lock_note, created_at, updated_at, published_at
    FROM public.mymodel_reflections;

    -- Remove default/previous grants before reproducing SELECT-only legacy access.
    -- The old view and shared table are never altered.
    REVOKE ALL ON public.mymodel_reflections_read FROM PUBLIC;
    FOR acl_row IN
        SELECT DISTINCT x.grantee, r.rolname
          FROM pg_catalog.pg_class c
          CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(c.relacl,
              pg_catalog.acldefault('r',c.relowner))) x
          JOIN pg_catalog.pg_roles r ON r.oid=x.grantee
         WHERE c.oid='public.mymodel_reflections_read'::regclass
           AND x.grantee<>relation_owner
    LOOP
        EXECUTE format('REVOKE ALL ON public.mymodel_reflections_read FROM %I', acl_row.rolname);
    END LOOP;
    FOR acl_row IN
        SELECT x.grantee, r.rolname, bool_or(x.is_grantable) AS grantable
          FROM pg_catalog.pg_class c
          CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(c.relacl,
              pg_catalog.acldefault('r',c.relowner))) x
          JOIN pg_catalog.pg_roles r ON r.oid=x.grantee
         WHERE c.oid=old_oid AND x.privilege_type='SELECT' AND x.grantee<>relation_owner
         GROUP BY x.grantee,r.rolname
    LOOP
        EXECUTE format('GRANT SELECT ON public.mymodel_reflections_read TO %I%s',
            acl_row.rolname, CASE WHEN acl_row.grantable THEN ' WITH GRANT OPTION' ELSE '' END);
    END LOOP;
END
$piece_bridge$;
