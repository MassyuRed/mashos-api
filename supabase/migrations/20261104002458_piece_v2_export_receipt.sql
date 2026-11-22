BEGIN;

-- Only hashes are added to the existing body-free ledger. Legacy rows are
-- retained, but cannot acknowledge an export under this new contract.
ALTER TABLE public.piece_export_receipts
    ADD COLUMN asset_sha256 text,
    ADD COLUMN request_identity_hash text,
    ADD CONSTRAINT piece_export_receipts_verified_hashes CHECK (
        (asset_sha256 IS NULL AND request_identity_hash IS NULL) OR
        (asset_sha256 IS NOT NULL AND asset_sha256 ~ '^[0-9a-f]{64}$' AND
         request_identity_hash IS NOT NULL AND request_identity_hash ~ '^[0-9a-f]{64}$' AND
         outcome = 'succeeded')
    );

CREATE FUNCTION public.piece_record_export_receipt_v2(
    p_owner_user_id uuid, p_piece_id uuid, p_expected_row_version bigint,
    p_idempotency_key_hash text, p_request_identity_hash text, p_piece_text_hash text,
    p_visual_recipe_hash text, p_asset_sha256 text, p_renderer_version text,
    p_output_profile text
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $receipt$
DECLARE
    r public.piece_records%ROWTYPE;
    receipt public.piece_export_receipts%ROWTYPE;
BEGIN
    IF p_owner_user_id IS NULL THEN RAISE EXCEPTION 'PIECE_AUTH_REQUIRED'; END IF;
    IF p_piece_id IS NULL OR coalesce(p_expected_row_version,0)<1 OR
       coalesce(p_idempotency_key_hash,'') !~ '^[0-9a-f]{64}$' OR
       coalesce(p_request_identity_hash,'') !~ '^[0-9a-f]{64}$' OR
       coalesce(p_piece_text_hash,'') !~ '^[0-9a-f]{64}$' OR
       coalesce(p_visual_recipe_hash,'') !~ '^[0-9a-f]{64}$' OR
       coalesce(p_asset_sha256,'') !~ '^[0-9a-f]{64}$' OR
       coalesce(p_renderer_version,'') NOT IN ('piece.rn_bitmap_renderer.ios.v1','piece.rn_bitmap_renderer.ios.v2') OR
       coalesce(p_output_profile,'') NOT IN ('png_1080x1350_srgb_v1','png_1080x1920_srgb_v1') THEN
        RAISE EXCEPTION 'PIECE_REQUEST_INVALID';
    END IF;

    SELECT * INTO r FROM public.piece_records
        WHERE id=p_piece_id AND owner_user_id=p_owner_user_id AND lifecycle_status='saved'
        FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'PIECE_NOT_FOUND'; END IF;
    IF r.row_version IS DISTINCT FROM p_expected_row_version OR
       r.piece_text_hash IS DISTINCT FROM p_piece_text_hash OR
       r.visual_recipe_hash IS DISTINCT FROM p_visual_recipe_hash OR
       r.renderer_version IS DISTINCT FROM p_renderer_version OR
       r.export_contract_version IS DISTINCT FROM 'piece.export_contract.v1' OR
       coalesce(r.safety_state,'') NOT IN ('ready','adjusted') OR
       (r.visual_recipe->>'visual_catalog_version') IS DISTINCT FROM 'piece.visual_catalog.v1' OR
       (r.visual_recipe->>'layout_policy_version') IS DISTINCT FROM 'piece.long_text_layout.v1' OR
       (CASE r.visual_recipe->>'aspect_ratio'
            WHEN '4:5' THEN 'png_1080x1350_srgb_v1'
            WHEN '9:16' THEN 'png_1080x1920_srgb_v1'
        END) IS DISTINCT FROM p_output_profile THEN
        RAISE EXCEPTION 'PIECE_CONFLICT';
    END IF;

    INSERT INTO public.piece_export_receipts(owner_user_id,piece_id,idempotency_key_hash,
        request_identity_hash,piece_text_hash,visual_recipe_hash,asset_sha256,outcome)
    VALUES(p_owner_user_id,p_piece_id,p_idempotency_key_hash,p_request_identity_hash,
        p_piece_text_hash,p_visual_recipe_hash,p_asset_sha256,'succeeded')
    ON CONFLICT (owner_user_id,idempotency_key_hash) DO NOTHING
    RETURNING * INTO receipt;

    IF NOT FOUND THEN
        SELECT * INTO receipt FROM public.piece_export_receipts
            WHERE owner_user_id=p_owner_user_id AND idempotency_key_hash=p_idempotency_key_hash;
        IF NOT FOUND OR receipt.piece_id IS DISTINCT FROM p_piece_id OR
           receipt.request_identity_hash IS DISTINCT FROM p_request_identity_hash OR
           receipt.piece_text_hash IS DISTINCT FROM p_piece_text_hash OR
           receipt.visual_recipe_hash IS DISTINCT FROM p_visual_recipe_hash OR
           receipt.asset_sha256 IS DISTINCT FROM p_asset_sha256 OR receipt.outcome<>'succeeded' THEN
            RAISE EXCEPTION 'PIECE_CONFLICT';
        END IF;
    END IF;
    RETURN jsonb_build_object('export_id',receipt.receipt_id);
END;
$receipt$;

DO $acl$
DECLARE
    signature constant text := 'public.piece_record_export_receipt_v2(uuid,uuid,bigint,text,text,text,text,text,text,text)';
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
