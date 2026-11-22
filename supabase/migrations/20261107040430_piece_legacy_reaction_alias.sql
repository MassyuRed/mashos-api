BEGIN;

-- Existing public Piece state only. Canonical/legacy aliases are derived from
-- the same current row that the API has already authorized; no client alias
-- list, dynamic table, data migration or public EXECUTE is accepted here.
CREATE FUNCTION public.piece_apply_legacy_reaction(
    p_source_id uuid, p_expected_owner uuid, p_viewer_id uuid,
    p_canonical_id text, p_q_key text, p_operation text,
    p_echo jsonb DEFAULT NULL
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $reaction$
DECLARE
    source_row record;
    canonical_id text;
    alias_ids text[];
    current_echo_id text;
    changed_id text;
    changed_count integer := 0;
    deleted_dates jsonb := '[]'::jsonb;
    total_views bigint;
    total_resonances bigint;
BEGIN
    IF p_source_id IS NULL OR p_expected_owner IS NULL OR p_viewer_id IS NULL OR
       p_expected_owner=p_viewer_id OR p_canonical_id IS NULL OR btrim(p_canonical_id)='' OR
       p_q_key IS NULL OR btrim(p_q_key)='' OR
       p_operation IS NULL OR p_operation NOT IN ('resonate','echo','remove') THEN
        RAISE EXCEPTION 'PIECE_REACTION_REQUEST_INVALID';
    END IF;
    -- Both aliases and all viewers of this public identity share one order.
    -- State and both counters commit together, including add/remove races.
    PERFORM pg_advisory_xact_lock(hashtextextended('piece-legacy-reaction:'||p_canonical_id,0));
    SELECT id,public_id,owner_user_id,q_key INTO source_row
      FROM public.mymodel_reflections
      WHERE id=p_source_id AND owner_user_id=p_expected_owner
        AND source_type='emotion_generated' AND is_active=true
        AND status IN ('ready','published')
      FOR SHARE;
    IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_REACTION_SOURCE_UNAVAILABLE'; END IF;
    canonical_id := coalesce(nullif(btrim(source_row.public_id),''),source_row.id::text);
    IF canonical_id NOT LIKE 'reflection:%' THEN canonical_id := 'reflection:'||canonical_id; END IF;
    IF canonical_id<>p_canonical_id OR
       (nullif(btrim(source_row.q_key),'') IS NOT NULL AND source_row.q_key<>p_q_key) THEN
        RAISE EXCEPTION 'PIECE_REACTION_SOURCE_BINDING';
    END IF;
    SELECT array_agg(DISTINCT alias_id ORDER BY alias_id) INTO alias_ids
      FROM unnest(ARRAY[canonical_id,substr(canonical_id,12),source_row.id::text,
                        'reflection:'||source_row.id::text]) AS aliases(alias_id);
    -- A pre-existing inconsistent key is not guessed or silently reassigned.
    IF EXISTS(SELECT 1 FROM public.mymodel_qna_metrics
              WHERE q_instance_id=ANY(alias_ids) AND q_key<>p_q_key)
       OR EXISTS(SELECT 1 FROM public.mymodel_qna_resonances
              WHERE viewer_user_id=p_viewer_id AND q_instance_id=ANY(alias_ids) AND q_key<>p_q_key)
       OR EXISTS(SELECT 1 FROM public.mymodel_qna_echoes
              WHERE viewer_user_id=p_viewer_id AND q_instance_id=ANY(alias_ids)
                AND (q_key<>p_q_key OR target_user_id<>p_expected_owner)) THEN
        RAISE EXCEPTION 'PIECE_REACTION_INSTANCE_KEY_CONFLICT';
    END IF;

    IF p_operation='echo' THEN
        IF p_echo IS NULL OR jsonb_typeof(p_echo)<>'object'
           OR NOT (p_echo ?& ARRAY['strength','memo','question','answer','topic_key','category'])
           OR EXISTS(SELECT 1 FROM jsonb_object_keys(p_echo) AS k
                     WHERE k NOT IN ('strength','memo','question','answer','topic_key','category'))
           OR p_echo->>'strength' IS NULL OR p_echo->>'strength' NOT IN ('small','medium','large')
           OR EXISTS(SELECT 1 FROM jsonb_each(p_echo) AS e
                     WHERE jsonb_typeof(e.value) NOT IN ('string','null'))
           OR length(coalesce(p_echo->>'memo',''))>2000 THEN
            RAISE EXCEPTION 'PIECE_REACTION_ECHO_INVALID';
        END IF;
        SELECT q_instance_id INTO current_echo_id FROM public.mymodel_qna_echoes
          WHERE viewer_user_id=p_viewer_id AND q_instance_id=ANY(alias_ids)
          ORDER BY created_at DESC,q_instance_id LIMIT 1;
        current_echo_id := coalesce(current_echo_id,canonical_id);
        INSERT INTO public.mymodel_qna_echoes(viewer_user_id,q_instance_id,target_user_id,
            question_id,q_key,strength,memo,context_source_type,context_question,
            context_answer,context_topic_key,context_category,created_at)
          VALUES(p_viewer_id,current_echo_id,p_expected_owner,0,p_q_key,p_echo->>'strength',
            p_echo->>'memo','emotion_generated',p_echo->>'question',p_echo->>'answer',
            p_echo->>'topic_key',p_echo->>'category',clock_timestamp())
          ON CONFLICT(viewer_user_id,q_instance_id) DO UPDATE SET
            target_user_id=excluded.target_user_id,question_id=excluded.question_id,
            q_key=excluded.q_key,strength=excluded.strength,memo=excluded.memo,
            context_source_type=excluded.context_source_type,context_question=excluded.context_question,
            context_answer=excluded.context_answer,context_topic_key=excluded.context_topic_key,
            context_category=excluded.context_category,created_at=excluded.created_at;
    END IF;

    IF p_operation IN ('resonate','echo') THEN
        IF NOT EXISTS(SELECT 1 FROM public.mymodel_qna_resonances
                      WHERE viewer_user_id=p_viewer_id AND q_instance_id=ANY(alias_ids)) THEN
            INSERT INTO public.mymodel_qna_resonances(viewer_user_id,q_instance_id,q_key,created_at)
              VALUES(p_viewer_id,canonical_id,p_q_key,clock_timestamp())
              ON CONFLICT(viewer_user_id,q_instance_id) DO NOTHING;
            GET DIAGNOSTICS changed_count=ROW_COUNT;
            IF changed_count=1 THEN
                PERFORM public.piece_increment_legacy_metric(p_q_key,canonical_id,'resonances',1);
            END IF;
        END IF;
    ELSE
        WITH removed AS (
          DELETE FROM public.mymodel_qna_echoes
            WHERE viewer_user_id=p_viewer_id AND q_instance_id=ANY(alias_ids)
            RETURNING created_at
        ) SELECT coalesce(jsonb_agg(created_at),'[]'::jsonb) INTO deleted_dates FROM removed;
        FOR changed_id IN DELETE FROM public.mymodel_qna_resonances
            WHERE viewer_user_id=p_viewer_id AND q_instance_id=ANY(alias_ids)
            RETURNING q_instance_id
        LOOP
            changed_count := changed_count+1;
            PERFORM public.piece_increment_legacy_metric(p_q_key,changed_id,'resonances',-1);
        END LOOP;
    END IF;
    SELECT coalesce(sum(views),0),coalesce(sum(resonances),0)
      INTO total_views,total_resonances FROM public.mymodel_qna_metrics
      WHERE q_instance_id=ANY(alias_ids) AND q_key=p_q_key;
    RETURN jsonb_build_object('q_instance_id',canonical_id,'changed_count',changed_count,
        'resonated',p_operation<>'remove','views',total_views,'resonances',total_resonances,
        'deleted_echo_activity_dates',deleted_dates);
END;
$reaction$;

DO $acl$
DECLARE
    signature constant text := 'public.piece_apply_legacy_reaction(uuid,uuid,uuid,text,text,text,jsonb)';
    entry record;
BEGIN
    EXECUTE 'REVOKE ALL ON FUNCTION '||signature||' FROM PUBLIC,anon,authenticated,service_role';
    FOR entry IN SELECT roles.rolname FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
        JOIN pg_catalog.pg_roles roles ON roles.oid=a.grantee
        WHERE p.oid=signature::regprocedure AND a.grantee<>p.proowner
    LOOP
        EXECUTE format('REVOKE ALL ON FUNCTION %s FROM %I',signature,entry.rolname);
    END LOOP;
    EXECUTE 'GRANT EXECUTE ON FUNCTION '||signature||' TO service_role';
END;
$acl$;

COMMIT;
