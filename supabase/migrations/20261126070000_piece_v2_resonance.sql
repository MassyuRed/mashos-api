-- Use the existing Piece resonance records and their viewer/piece uniqueness.
-- PRODUCTION_APPLICATION_REQUIRES_SEPARATE_MASH_APPROVAL
BEGIN;

ALTER TABLE public.piece_record_resonances
    ADD CONSTRAINT piece_record_resonances_viewer_auth_fk
    FOREIGN KEY (viewer_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE FUNCTION public.piece_set_resonance_v2(
    p_viewer_user_id uuid, p_piece_id uuid, p_resonated boolean
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $resonance$
DECLARE
    target_owner_id uuid;
    target_source_id uuid;
BEGIN
    IF p_viewer_user_id IS NULL OR p_piece_id IS NULL OR p_resonated IS NULL THEN
        RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
    END IF;

    -- The publisher locks the Piece before its source. Use the same order.
    SELECT r.owner_user_id,
           CASE WHEN r.source_input_id ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
                THEN r.source_input_id::uuid END
    INTO target_owner_id, target_source_id
    FROM public.piece_records r
    WHERE r.id=p_piece_id AND r.owner_user_id<>p_viewer_user_id
      AND r.lifecycle_status='saved' AND r.visibility_scope='public'
    FOR UPDATE OF r;
    IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;

    PERFORM 1 FROM public.emotions e
    WHERE e.id=target_source_id AND e.user_id=target_owner_id AND e.is_secret IS FALSE
    FOR SHARE OF e;
    IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;

    -- Author privacy edits take a key-share lock on the link. Read the author
    -- setting after acquiring this lock so a pending edit cannot be bypassed.
    PERFORM 1 FROM public.myprofile_links l
    WHERE l.owner_user_id=target_owner_id AND l.viewer_user_id=p_viewer_user_id
    FOR UPDATE OF l;
    IF NOT FOUND OR EXISTS (
        SELECT 1 FROM public.follow_author_visibility_overrides v
        WHERE v.author_user_id=target_owner_id AND v.follower_user_id=p_viewer_user_id AND NOT v.can_view_pieces
    ) THEN
        RAISE EXCEPTION 'PIECE_NOT_FOUND';
    END IF;

    IF p_resonated THEN
        INSERT INTO public.piece_record_resonances(piece_id, owner_user_id, viewer_user_id)
        VALUES (p_piece_id, target_owner_id, p_viewer_user_id)
        ON CONFLICT (piece_id, viewer_user_id) DO NOTHING;
    ELSE
        DELETE FROM public.piece_record_resonances
        WHERE piece_id=p_piece_id AND viewer_user_id=p_viewer_user_id;
    END IF;

    RETURN jsonb_build_object(
        'public_id', 'piece:' || p_piece_id::text, 'resonated', p_resonated,
        'resonances', (SELECT count(*) FROM public.piece_record_resonances WHERE piece_id=p_piece_id)
    );
END;
$resonance$;

CREATE FUNCTION public.piece_read_resonance_feed_v2(
    p_viewer_user_id uuid, p_target_owner_user_id uuid, p_following_only boolean,
    p_sort text, p_limit integer
) RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog
AS $resonance_feed$
    SELECT coalesce(jsonb_agg(item || jsonb_build_object(
        'resonances', (SELECT count(*) FROM public.piece_record_resonances r WHERE r.piece_id=ids.piece_id),
        'is_resonated', EXISTS (
            SELECT 1 FROM public.piece_record_resonances r
            WHERE r.piece_id=ids.piece_id AND r.viewer_user_id=p_viewer_user_id
        ),
        'can_resonate', (item->>'owner_user_id')::uuid<>p_viewer_user_id
    ) ORDER BY ord), '[]'::jsonb)
    FROM jsonb_array_elements(public.piece_read_public_feed_v2(
        p_viewer_user_id, p_target_owner_user_id, p_following_only, p_sort, p_limit
    )) WITH ORDINALITY AS feed(item, ord)
    CROSS JOIN LATERAL (SELECT substr(item->>'public_id', 7)::uuid AS piece_id) ids;
$resonance_feed$;

CREATE FUNCTION public.piece_read_resonance_history_v2(
    p_viewer_user_id uuid, p_order text, p_limit integer, p_offset bigint,
    p_since timestamptz, p_until timestamptz
) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog
AS $resonance_history$
DECLARE result jsonb;
BEGIN
    IF p_viewer_user_id IS NULL OR p_order IS NULL OR p_order NOT IN ('newest','oldest')
       OR p_limit IS NULL OR p_limit NOT BETWEEN 1 AND 4100
       OR p_offset IS NULL OR p_offset<0 OR p_since>=p_until THEN
        RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
    END IF;

    WITH visible AS MATERIALIZED (
        SELECT r.id, r.public_id, r.owner_user_id, r.piece_text, r.updated_at AS published_at, rr.created_at AS saved_at
        FROM public.piece_record_resonances rr
        JOIN public.piece_records r ON r.id=rr.piece_id AND r.owner_user_id=rr.owner_user_id
        JOIN public.emotions e ON e.user_id=r.owner_user_id AND e.is_secret IS FALSE
         AND e.id=CASE WHEN r.source_input_id ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
                       THEN r.source_input_id::uuid END
        JOIN public.follow_author_visibility_effective_v1 v
          ON v.author_user_id=r.owner_user_id AND v.follower_user_id=rr.viewer_user_id AND v.can_view_pieces
        WHERE rr.viewer_user_id=p_viewer_user_id AND r.lifecycle_status='saved' AND r.visibility_scope='public'
          AND (p_since IS NULL OR rr.created_at>=p_since)
          AND (p_until IS NULL OR rr.created_at<p_until)
    ), page AS (
        SELECT *
        FROM visible
        ORDER BY
            CASE WHEN p_order='newest' THEN saved_at END DESC,
            CASE WHEN p_order='oldest' THEN saved_at END ASC,
            CASE WHEN p_order='newest' THEN public_id END DESC,
            CASE WHEN p_order='oldest' THEN public_id END ASC
        LIMIT p_limit OFFSET p_offset
    )
    SELECT jsonb_build_object(
        'total_items', (SELECT count(*) FROM visible),
        'items', coalesce(jsonb_agg(jsonb_build_object(
            'public_id', page.public_id, 'owner_user_id', page.owner_user_id, 'body', page.piece_text,
            'published_at', page.published_at, 'saved_at', page.saved_at,
            'resonances', (SELECT count(*) FROM public.piece_record_resonances rr WHERE rr.piece_id=page.id),
            'is_resonated', true, 'can_resonate', true
        ) ORDER BY
            CASE WHEN p_order='newest' THEN page.saved_at END DESC,
            CASE WHEN p_order='oldest' THEN page.saved_at END ASC,
            CASE WHEN p_order='newest' THEN page.public_id END DESC,
            CASE WHEN p_order='oldest' THEN page.public_id END ASC
        ), '[]'::jsonb)
    ) INTO result
    FROM page;
    RETURN result;
END;
$resonance_history$;

REVOKE ALL ON FUNCTION public.piece_set_resonance_v2(uuid,uuid,boolean),
    public.piece_read_resonance_feed_v2(uuid,uuid,boolean,text,integer),
    public.piece_read_resonance_history_v2(uuid,text,integer,bigint,timestamptz,timestamptz)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.piece_set_resonance_v2(uuid,uuid,boolean),
    public.piece_read_resonance_feed_v2(uuid,uuid,boolean,text,integer),
    public.piece_read_resonance_history_v2(uuid,text,integer,bigint,timestamptz,timestamptz)
    TO service_role;

COMMIT;
