-- Overrides belong to the author and do not disappear when the follower leaves.
-- Only current directed follow links grant any access. Absence of an override
-- retains the existing visibility for that active link.
BEGIN;

CREATE TABLE public.follow_author_visibility_overrides (
    author_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    follower_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    can_view_pieces boolean NOT NULL DEFAULT true,
    can_receive_emotion_notifications boolean NOT NULL DEFAULT true,
    PRIMARY KEY (author_user_id, follower_user_id),
    CHECK (author_user_id <> follower_user_id)
);
ALTER TABLE public.follow_author_visibility_overrides ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.follow_author_visibility_overrides FROM PUBLIC, anon, authenticated, service_role;

CREATE VIEW public.follow_author_visibility_effective_v1
WITH (security_invoker=true) AS
SELECT l.owner_user_id AS author_user_id, l.viewer_user_id AS follower_user_id,
       coalesce(o.can_view_pieces, true) AS can_view_pieces,
       coalesce(o.can_receive_emotion_notifications, true) AS can_receive_emotion_notifications
FROM public.myprofile_links l
LEFT JOIN public.follow_author_visibility_overrides o
       ON o.author_user_id=l.owner_user_id AND o.follower_user_id=l.viewer_user_id;
REVOKE ALL ON public.follow_author_visibility_effective_v1 FROM PUBLIC, anon, authenticated, service_role;

-- Old/direct readers of the physical feed must honor an author revocation too.
-- Only the JWT viewer's own relationship is checked by this RLS helper.
CREATE SCHEMA follow_visibility_internal;
REVOKE ALL ON SCHEMA follow_visibility_internal FROM PUBLIC, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA follow_visibility_internal TO authenticated;

CREATE FUNCTION follow_visibility_internal.can_read_author_emotion_feed(p_author_user_id uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $client_feed$
    SELECT EXISTS (
        SELECT 1 FROM public.follow_author_visibility_effective_v1 v
        WHERE v.follower_user_id=(SELECT auth.uid())
          AND v.author_user_id=p_author_user_id AND v.can_receive_emotion_notifications
    );
$client_feed$;
REVOKE ALL ON FUNCTION follow_visibility_internal.can_read_author_emotion_feed(uuid)
    FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION follow_visibility_internal.can_read_author_emotion_feed(uuid)
    TO authenticated;

ALTER POLICY viewer_can_select_own_feed ON public.friend_emotion_feed TO authenticated
    USING (viewer_user_id=(SELECT auth.uid()) AND
           follow_visibility_internal.can_read_author_emotion_feed(owner_user_id));

CREATE FUNCTION public.follow_author_visibility_list_v1(p_author_user_id uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $list$
    SELECT coalesce(jsonb_agg(jsonb_build_object(
        'follower_user_id', v.follower_user_id,
        'can_view_pieces', v.can_view_pieces,
        'can_receive_emotion_notifications', v.can_receive_emotion_notifications
    ) ORDER BY v.follower_user_id), '[]'::jsonb)
    FROM public.follow_author_visibility_effective_v1 v
    WHERE v.author_user_id=p_author_user_id;
$list$;

CREATE FUNCTION public.follow_author_visibility_patch_v1(
    p_author_user_id uuid, p_follower_user_id uuid,
    p_can_view_pieces boolean, p_can_receive_emotion_notifications boolean
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $patch$
DECLARE updated public.follow_author_visibility_overrides%ROWTYPE;
BEGIN
    IF p_author_user_id IS NULL OR p_follower_user_id IS NULL OR p_author_user_id=p_follower_user_id
       OR (p_can_view_pieces IS NULL AND p_can_receive_emotion_notifications IS NULL) THEN
        RAISE EXCEPTION 'FOLLOW_VISIBILITY_INVALID';
    END IF;

    PERFORM 1 FROM public.myprofile_links l
      WHERE l.owner_user_id=p_author_user_id AND l.viewer_user_id=p_follower_user_id
      FOR KEY SHARE OF l;
    IF NOT FOUND THEN RAISE EXCEPTION 'FOLLOW_RELATION_NOT_FOUND'; END IF;

    INSERT INTO public.follow_author_visibility_overrides AS current_choice
        (author_user_id, follower_user_id, can_view_pieces, can_receive_emotion_notifications)
    VALUES (p_author_user_id, p_follower_user_id, coalesce(p_can_view_pieces, true),
            coalesce(p_can_receive_emotion_notifications, true))
    ON CONFLICT (author_user_id, follower_user_id) DO UPDATE SET
        can_view_pieces=coalesce(p_can_view_pieces, current_choice.can_view_pieces),
        can_receive_emotion_notifications=coalesce(p_can_receive_emotion_notifications,
                                                  current_choice.can_receive_emotion_notifications)
    RETURNING * INTO updated;

    RETURN jsonb_build_object(
        'follower_user_id', updated.follower_user_id,
        'can_view_pieces', updated.can_view_pieces,
        'can_receive_emotion_notifications', updated.can_receive_emotion_notifications
    );
END;
$patch$;

CREATE FUNCTION public.follow_piece_visible_owner_ids_v1(p_viewer_user_id uuid, p_owner_user_ids uuid[])
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $piece_viewers$
    SELECT coalesce(jsonb_agg(allowed.author_user_id ORDER BY allowed.author_user_id), '[]'::jsonb)
    FROM (
        SELECT DISTINCT candidate.author_user_id
        FROM unnest(p_owner_user_ids) AS candidate(author_user_id)
        WHERE candidate.author_user_id=p_viewer_user_id
           OR EXISTS (
               SELECT 1 FROM public.follow_author_visibility_effective_v1 v
               WHERE v.follower_user_id=p_viewer_user_id AND v.author_user_id=candidate.author_user_id
                 AND v.can_view_pieces
           )
    ) allowed;
$piece_viewers$;

CREATE FUNCTION public.emotion_notification_recipients_allowed(p_owner_user_id uuid, p_viewer_user_ids uuid[])
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $emotion_recipients$
    SELECT coalesce(jsonb_agg(v.follower_user_id ORDER BY v.follower_user_id), '[]'::jsonb)
    FROM public.follow_author_visibility_effective_v1 v
    WHERE v.author_user_id=p_owner_user_id AND v.follower_user_id=ANY(p_viewer_user_ids)
      AND v.can_receive_emotion_notifications;
$emotion_recipients$;

CREATE FUNCTION public.emotion_log_feed_for_viewer(p_viewer_user_id uuid, p_limit integer)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $emotion_feed$
DECLARE result jsonb;
BEGIN
    IF p_viewer_user_id IS NULL OR p_limit IS NULL OR p_limit NOT BETWEEN 1 AND 200 THEN
        RAISE EXCEPTION 'FOLLOW_VISIBILITY_INVALID';
    END IF;
    SELECT coalesce(jsonb_agg(jsonb_build_object(
        'id', feed.id, 'viewer_user_id', feed.viewer_user_id,
        'owner_user_id', feed.owner_user_id, 'owner_name', feed.owner_name,
        'items', feed.items, 'created_at', feed.created_at
    ) ORDER BY feed.created_at DESC, feed.id DESC), '[]'::jsonb)
    INTO result
    FROM (
        SELECT f.id, f.viewer_user_id, f.owner_user_id, f.owner_name, f.items, f.created_at
        FROM public.friend_emotion_feed f
        JOIN public.follow_author_visibility_effective_v1 v
          ON v.follower_user_id=f.viewer_user_id AND v.author_user_id=f.owner_user_id
        WHERE f.viewer_user_id=p_viewer_user_id AND v.can_receive_emotion_notifications
        ORDER BY f.created_at DESC, f.id DESC
        LIMIT p_limit
    ) feed;
    RETURN result;
END;
$emotion_feed$;

CREATE OR REPLACE FUNCTION public.piece_read_public_feed_v2(
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
        -- On saved Piece records updated_at is the visibility change time.
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
                  SELECT 1 FROM public.follow_author_visibility_effective_v1 v
                  WHERE v.follower_user_id=p_viewer_user_id AND v.author_user_id=r.owner_user_id
                    AND v.can_view_pieces
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

REVOKE ALL ON FUNCTION public.follow_author_visibility_list_v1(uuid),
    public.follow_author_visibility_patch_v1(uuid,uuid,boolean,boolean),
    public.follow_piece_visible_owner_ids_v1(uuid,uuid[]),
    public.emotion_notification_recipients_allowed(uuid,uuid[]),
    public.emotion_log_feed_for_viewer(uuid,integer),
    public.piece_read_public_feed_v2(uuid,uuid,boolean,text,integer)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.follow_author_visibility_list_v1(uuid),
    public.follow_author_visibility_patch_v1(uuid,uuid,boolean,boolean),
    public.follow_piece_visible_owner_ids_v1(uuid,uuid[]),
    public.emotion_notification_recipients_allowed(uuid,uuid[]),
    public.emotion_log_feed_for_viewer(uuid,integer),
    public.piece_read_public_feed_v2(uuid,uuid,boolean,text,integer)
    TO service_role;

COMMIT;
