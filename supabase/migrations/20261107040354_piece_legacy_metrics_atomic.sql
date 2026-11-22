BEGIN;

-- Existing legacy public counters only. The Piece V2 record tables and the
-- backend-readonly piece_metrics bridge keep their current responsibilities.
-- The partial unique indexes already own the global/instance identities.
CREATE FUNCTION public.piece_increment_legacy_metric(
    p_q_key text, p_q_instance_id text, p_field text, p_delta integer
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $metric$
DECLARE
    global_row public.mymodel_qna_metrics%ROWTYPE;
    instance_row public.mymodel_qna_metrics%ROWTYPE;
    add_views bigint;
    add_resonances bigint;
BEGIN
    IF p_q_key IS NULL OR btrim(p_q_key)='' OR
       (p_q_instance_id IS NOT NULL AND btrim(p_q_instance_id)='') OR
       p_field IS NULL OR p_field NOT IN ('views','resonances') OR
       p_delta IS NULL OR p_delta NOT IN (-1,1) THEN
        RAISE EXCEPTION 'PIECE_METRIC_REQUEST_INVALID';
    END IF;
    add_views := CASE WHEN p_field='views' THEN p_delta ELSE 0 END;
    add_resonances := CASE WHEN p_field='resonances' THEN p_delta ELSE 0 END;

    -- Take the shared global row first on every call. Both increments are in
    -- this transaction, so neither concurrent writers nor a failed instance
    -- binding can commit only one half of the update.
    INSERT INTO public.mymodel_qna_metrics(q_key,q_instance_id,views,resonances,updated_at)
        VALUES(p_q_key,NULL,greatest(0,add_views),greatest(0,add_resonances),clock_timestamp())
    ON CONFLICT (q_key) WHERE q_instance_id IS NULL DO UPDATE SET
        views=greatest(0,public.mymodel_qna_metrics.views+add_views),
        resonances=greatest(0,public.mymodel_qna_metrics.resonances+add_resonances),
        updated_at=clock_timestamp()
    RETURNING * INTO global_row;

    IF p_q_instance_id IS NULL THEN
        RETURN jsonb_build_object('views',global_row.views,'resonances',global_row.resonances);
    END IF;
    INSERT INTO public.mymodel_qna_metrics(q_key,q_instance_id,views,resonances,updated_at)
        VALUES(p_q_key,p_q_instance_id,greatest(0,add_views),greatest(0,add_resonances),clock_timestamp())
    ON CONFLICT (q_instance_id) WHERE q_instance_id IS NOT NULL DO UPDATE SET
        views=greatest(0,public.mymodel_qna_metrics.views+add_views),
        resonances=greatest(0,public.mymodel_qna_metrics.resonances+add_resonances),
        updated_at=clock_timestamp()
    WHERE public.mymodel_qna_metrics.q_key=excluded.q_key
    RETURNING * INTO instance_row;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'PIECE_METRIC_INSTANCE_KEY_CONFLICT';
    END IF;
    RETURN jsonb_build_object('views',instance_row.views,'resonances',instance_row.resonances,
        'global_views',global_row.views,'global_resonances',global_row.resonances);
END;
$metric$;

DO $acl$
DECLARE
    signature constant text := 'public.piece_increment_legacy_metric(text,text,text,integer)';
    entry record;
BEGIN
    EXECUTE 'REVOKE ALL ON FUNCTION ' || signature || ' FROM PUBLIC, anon, authenticated, service_role';
    FOR entry IN SELECT roles.rolname
        FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
        JOIN pg_catalog.pg_roles roles ON roles.oid=a.grantee
        WHERE p.oid=signature::regprocedure AND a.grantee<>p.proowner
    LOOP
        EXECUTE format('REVOKE ALL ON FUNCTION %s FROM %I',signature,entry.rolname);
    END LOOP;
    EXECUTE 'GRANT EXECUTE ON FUNCTION ' || signature || ' TO service_role';
END;
$acl$;

COMMIT;
