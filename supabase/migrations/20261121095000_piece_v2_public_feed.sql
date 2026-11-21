-- Saved Piece publication uses the existing owner+row-version mutation.
-- Feed authorization and projection are evaluated together on every read.
BEGIN;

CREATE FUNCTION public.piece_read_public_feed_v2(
    p_viewer_user_id uuid, p_target_owner_user_id uuid, p_following_only boolean,
    p_sort text, p_limit integer
) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog
AS $public_feed$
DECLARE result jsonb;
BEGIN
    IF p_viewer_user_id IS NULL THEN RAISE EXCEPTION 'PIECE_AUTH_REQUIRED'; END IF;
    IF p_following_only IS NULL OR p_sort IS NULL OR p_sort NOT IN ('latest', 'oldest')
       OR p_limit IS NULL OR p_limit NOT BETWEEN 1 AND 101 THEN
        RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
    END IF;

    SELECT coalesce(jsonb_agg(jsonb_build_object(
        'public_id', feed.public_id, 'owner_user_id', feed.owner_user_id,
        'body', feed.piece_text, 'published_at', feed.published_at
    ) ORDER BY
        CASE WHEN p_sort='latest' THEN feed.published_at END DESC,
        CASE WHEN p_sort='oldest' THEN feed.published_at END ASC,
        feed.public_id), '[]'::jsonb)
    INTO result
    FROM (
        -- For saved records updated_at tracks the visibility change (or an initial public save).
        SELECT r.public_id, r.owner_user_id, r.piece_text, r.updated_at AS published_at
        FROM public.piece_records r
        JOIN public.emotions e ON e.user_id=r.owner_user_id AND e.is_secret IS FALSE
         AND e.id=CASE WHEN r.source_input_id ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
                       THEN r.source_input_id::uuid END
        WHERE r.lifecycle_status='saved' AND r.visibility_scope='public'
          AND (p_target_owner_user_id IS NULL OR r.owner_user_id=p_target_owner_user_id)
          AND (
              (r.owner_user_id=p_viewer_user_id AND
               (p_target_owner_user_id IS NOT NULL OR NOT p_following_only))
              OR EXISTS (
                  SELECT 1 FROM public.myprofile_links l
                  WHERE l.viewer_user_id=p_viewer_user_id AND l.owner_user_id=r.owner_user_id
              )
          )
        ORDER BY
            CASE WHEN p_sort='latest' THEN r.updated_at END DESC,
            CASE WHEN p_sort='oldest' THEN r.updated_at END ASC,
            r.public_id
        LIMIT p_limit
    ) feed;
    RETURN result;
END;
$public_feed$;

CREATE OR REPLACE FUNCTION public.piece_set_visibility_v2(
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
    IF p_visibility_scope='public' THEN
        PERFORM 1 FROM public.emotions e
        WHERE e.user_id=p_owner_user_id AND e.is_secret IS FALSE
          AND e.id=CASE WHEN r.source_input_id ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
                        THEN r.source_input_id::uuid END
        FOR SHARE OF e;
        IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_PUBLICATION_NOT_ALLOWED'; END IF;
    END IF;
    IF r.visibility_scope=p_visibility_scope THEN
        RETURN jsonb_build_object('piece_id',r.id,'visibility_scope',r.visibility_scope,'row_version',r.row_version);
    END IF;
    UPDATE public.piece_records SET visibility_scope=p_visibility_scope,
        row_version=row_version+1,updated_at=clock_timestamp() WHERE id=r.id RETURNING * INTO r;
    RETURN jsonb_build_object('piece_id',r.id,'visibility_scope',r.visibility_scope,'row_version',r.row_version);
END;
$visibility$;

REVOKE ALL ON FUNCTION public.piece_read_public_feed_v2(uuid,uuid,boolean,text,integer)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.piece_read_public_feed_v2(uuid,uuid,boolean,text,integer)
    TO service_role;
REVOKE ALL ON FUNCTION public.piece_set_visibility_v2(uuid,uuid,bigint,text)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.piece_set_visibility_v2(uuid,uuid,bigint,text)
    TO service_role;

COMMIT;
