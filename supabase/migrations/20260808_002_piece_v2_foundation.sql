-- migration_id: 20260808_002_piece_v2_foundation
-- B2-B / M2 FILE-ONLY CANDIDATE. No production application is authorized.
-- Owners: piece.data_contract.v1; piece.source_lineage.v1;
-- piece.record_lifecycle.v1; piece.quota_consumption.v1 (PCE-2/3/6/8).
-- Requires the separately verified M1 bridge. Does not replace public.pieces.
-- One atomic statement; pre-existing target objects cause STOP, not adoption.
-- B3/B4 own access policies, service grants, atomic save/quota/delete and
-- immutable saved-record operations. This foundation exposes no API or RPC.
-- Content/recipe canonical JSON validation remains the existing B1/B8/B9
-- author's responsibility: PostgreSQL jsonb::text is NOT that canonical JSON.
-- Rollback verification is transaction rollback on a disposable database.
-- No automatic down/drop/data cleanup or live migration is supplied here.
-- PRODUCTION_APPLICATION_REQUIRES_SEPARATE_MASH_APPROVAL
DO $piece_foundation$
DECLARE
    table_name text;
    role_name text;
    acl_entry record;
    bridge_oid oid := pg_catalog.to_regclass('public.mymodel_reflections_read');
    targets text[] := ARRAY['piece_records','piece_quota_month_locks',
        'piece_quota_consumptions','piece_record_metrics','piece_record_reads',
        'piece_record_resonances','piece_export_receipts','piece_delete_receipts'];
BEGIN
    IF current_setting('server_version_num')::integer < 150000 THEN
        RAISE EXCEPTION 'PIECE_M2_PRECONDITION: PostgreSQL 15 or later required';
    END IF;
    IF bridge_oid IS NULL OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class WHERE oid = bridge_oid AND relkind = 'v'
          AND 'security_invoker=true' = ANY(coalesce(reloptions, ARRAY[]::text[]))
    ) THEN
        RAISE EXCEPTION 'PIECE_M2_PRECONDITION: verified M1 bridge required';
    END IF;
    FOREACH role_name IN ARRAY ARRAY['anon','authenticated','service_role'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = role_name) THEN
            RAISE EXCEPTION 'PIECE_M2_PRECONDITION: application roles required';
        END IF;
    END LOOP;
    FOREACH table_name IN ARRAY targets LOOP
        IF pg_catalog.to_regclass('public.' || table_name) IS NOT NULL THEN
            RAISE EXCEPTION 'PIECE_M2_TARGET_EXISTS: %', table_name;
        END IF;
    END LOOP;

    CREATE TABLE public.piece_records (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        public_id text GENERATED ALWAYS AS ('piece:' || id::text) STORED UNIQUE,
        owner_user_id uuid NOT NULL,
        piece_contract_version text NOT NULL DEFAULT 'piece.record.v2'
            CHECK (piece_contract_version = 'piece.record.v2'),
        source_lineage_version text NOT NULL DEFAULT 'piece.source_lineage.v1'
            CHECK (source_lineage_version = 'piece.source_lineage.v1'),
        source_input_id text NOT NULL CHECK (length(btrim(source_input_id)) > 0),
        source_input_version text NOT NULL CHECK (length(btrim(source_input_version)) > 0),
        source_input_bundle_commitment text NOT NULL
            CHECK (source_input_bundle_commitment ~ '^sha256:[0-9a-f]{64}$'),
        source_lineage jsonb NOT NULL,
        lifecycle_status text NOT NULL DEFAULT 'preview_draft'
            CHECK (lifecycle_status IN ('preview_draft','saved','cancelled','rejected','expired','deleted')),
        visibility_scope text NOT NULL DEFAULT 'private'
            CHECK (visibility_scope IN ('private','public')),
        preview_revision bigint NOT NULL DEFAULT 1 CHECK (preview_revision > 0),
        row_version bigint NOT NULL DEFAULT 1 CHECK (row_version > 0),
        expires_at timestamptz,
        saved_at timestamptz,
        save_idempotency_key_hash text
            CHECK (save_idempotency_key_hash ~ '^[0-9a-f]{64}$'),
        format_type text NOT NULL CHECK (format_type IN ('short_essay','quote','declaration')),
        content_payload_version text NOT NULL DEFAULT 'piece.content_payload.v1'
            CHECK (content_payload_version = 'piece.content_payload.v1'),
        content_meaning_version text NOT NULL DEFAULT 'piece.content_meaning.v1'
            CHECK (content_meaning_version = 'piece.content_meaning.v1'),
        content_payload jsonb NOT NULL,
        content_payload_hash text NOT NULL CHECK (content_payload_hash ~ '^[0-9a-f]{64}$'),
        piece_text text NOT NULL CHECK (length(btrim(piece_text)) > 0),
        piece_text_hash text NOT NULL CHECK (piece_text_hash ~ '^[0-9a-f]{64}$')
            CHECK (piece_text_hash = pg_catalog.encode(
                pg_catalog.sha256(pg_catalog.convert_to(piece_text, 'UTF8')), 'hex')),
        safety_contract_version text NOT NULL DEFAULT 'piece.public_safety_transformation.v1'
            CHECK (safety_contract_version = 'piece.public_safety_transformation.v1'),
        safety_state text NOT NULL CHECK (safety_state IN ('ready','adjusted')),
        visual_recipe jsonb NOT NULL,
        visual_recipe_hash text NOT NULL CHECK (visual_recipe_hash ~ '^[0-9a-f]{64}$'),
        visual_recipe_version text NOT NULL DEFAULT 'piece.visual_recipe.v1'
            CHECK (visual_recipe_version = 'piece.visual_recipe.v1'),
        visual_catalog_version text NOT NULL DEFAULT 'piece.visual_catalog.v1'
            CHECK (visual_catalog_version = 'piece.visual_catalog.v1'),
        export_contract_version text NOT NULL DEFAULT 'piece.export_contract.v1'
            CHECK (export_contract_version = 'piece.export_contract.v1'),
        render_interface_version text NOT NULL DEFAULT 'piece.render_interface.v1'
            CHECK (render_interface_version = 'piece.render_interface.v1'),
        render_reproducibility_version text NOT NULL DEFAULT 'piece.render_reproducibility.v1'
            CHECK (render_reproducibility_version = 'piece.render_reproducibility.v1'),
        layout_policy_version text NOT NULL DEFAULT 'piece.long_text_layout.v1'
            CHECK (layout_policy_version = 'piece.long_text_layout.v1'),
        renderer_version text NOT NULL CHECK (length(btrim(renderer_version)) > 0),
        created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        CONSTRAINT piece_records_owner_identity UNIQUE (id, owner_user_id),
        CONSTRAINT piece_records_save_identity UNIQUE (owner_user_id, save_idempotency_key_hash),
        CONSTRAINT piece_records_saved_shape CHECK (
            (lifecycle_status NOT IN ('saved','deleted') AND saved_at IS NULL
                AND save_idempotency_key_hash IS NULL AND visibility_scope = 'private')
            OR (lifecycle_status IN ('saved','deleted') AND saved_at IS NOT NULL
                AND save_idempotency_key_hash IS NOT NULL AND expires_at IS NULL)
        ),
        CONSTRAINT piece_records_preview_expiry CHECK (
            lifecycle_status <> 'preview_draft' OR expires_at IS NOT NULL
        ),
        -- Deleted is an in-transaction terminal state. B4 must physically purge
        -- the row before commit; M2 does not claim a delete RPC is implemented.
        CONSTRAINT piece_records_lineage_binding CHECK ((
            jsonb_typeof(source_lineage) = 'object'
            AND source_lineage ?& ARRAY['handoff_contract_version','piece_source_lineage_version',
                'source_input','observation','semantic_source_roles','lineage_control_roles',
                'piece_generation_eligibility','body_free']
            AND source_lineage - ARRAY['handoff_contract_version','piece_source_lineage_version',
                'source_input','observation','semantic_source_roles','lineage_control_roles',
                'piece_generation_eligibility','body_free'] = '{}'::jsonb
            AND source_lineage->>'handoff_contract_version' = 'cocolon.cross_core.source_handoff.v1'
            AND source_lineage->>'piece_source_lineage_version' = source_lineage_version
            AND source_lineage->'body_free' = 'true'::jsonb
            AND jsonb_typeof(source_lineage->'source_input') = 'object'
            AND (source_lineage->'source_input') ?& ARRAY['source_input_id','source_input_version',
                'source_input_bundle_commitment','source_owner_user_id','source_recorded_at']
            AND (source_lineage->'source_input') - ARRAY['source_input_id','source_input_version',
                'source_input_bundle_commitment','source_owner_user_id','source_recorded_at'] = '{}'::jsonb
            AND source_lineage#>>'{source_input,source_input_id}' = source_input_id
            AND source_lineage#>>'{source_input,source_input_version}' = source_input_version
            AND source_lineage#>>'{source_input,source_input_bundle_commitment}' = source_input_bundle_commitment
            AND source_lineage#>>'{source_input,source_owner_user_id}' = owner_user_id::text
            AND jsonb_typeof(source_lineage#>'{source_input,source_recorded_at}') = 'string'
            AND length(source_lineage#>>'{source_input,source_recorded_at}') > 0
            AND jsonb_typeof(source_lineage->'observation') = 'object'
            AND (source_lineage->'observation') ?& ARRAY['emlis_observation_stage',
                'emlis_observation_result_identity','emlis_observation_result_state',
                'question_need_decision_identity','supplemental_answer_identity',
                'supplemental_answer_version','supplemental_answer_bundle_commitment']
            AND (source_lineage->'observation') - ARRAY['emlis_observation_stage',
                'emlis_observation_result_identity','emlis_observation_result_state',
                'question_need_decision_identity','supplemental_answer_identity',
                'supplemental_answer_version','supplemental_answer_bundle_commitment'] = '{}'::jsonb
            AND jsonb_typeof(source_lineage#>'{observation,emlis_observation_result_identity}') = 'string'
            AND length(source_lineage#>>'{observation,emlis_observation_result_identity}') > 0
            AND source_lineage#>>'{observation,emlis_observation_result_state}' = 'terminal_success'
            AND jsonb_typeof(source_lineage->'piece_generation_eligibility') = 'object'
            AND (source_lineage->'piece_generation_eligibility') ?& ARRAY['contract_version','decision','reason_codes']
            AND (source_lineage->'piece_generation_eligibility') - ARRAY['contract_version','decision','reason_codes'] = '{}'::jsonb
            AND source_lineage#>>'{piece_generation_eligibility,contract_version}' = 'piece.generation_eligibility.v1'
            AND source_lineage#>>'{piece_generation_eligibility,decision}' = 'eligible'
            AND jsonb_typeof(source_lineage#>'{piece_generation_eligibility,reason_codes}') = 'array'
        ) IS TRUE),
        CONSTRAINT piece_records_source_stage CHECK ((
            (source_lineage#>>'{observation,emlis_observation_stage}' = 'normal_observation'
                AND source_lineage->'semantic_source_roles' = '["original_input"]'::jsonb
                AND source_lineage->'lineage_control_roles' = '["emlis_observation_result"]'::jsonb
                AND source_lineage#>'{observation,question_need_decision_identity}' = 'null'::jsonb)
            OR (source_lineage#>>'{observation,emlis_observation_stage}' IN ('pre_question_observation','refined_observation')
                AND source_lineage->'lineage_control_roles' = '["emlis_observation_result","question_need_decision"]'::jsonb
                AND jsonb_typeof(source_lineage#>'{observation,question_need_decision_identity}') = 'string'
                AND length(source_lineage#>>'{observation,question_need_decision_identity}') > 0
                AND source_lineage->'semantic_source_roles' = CASE
                    WHEN source_lineage#>>'{observation,emlis_observation_stage}' = 'refined_observation'
                    THEN '["original_input","supplemental_answer"]'::jsonb ELSE '["original_input"]'::jsonb END)
        ) IS TRUE),
        CONSTRAINT piece_records_supplemental_boundary CHECK ((
            CASE WHEN source_lineage#>>'{observation,emlis_observation_stage}' = 'refined_observation' THEN
                jsonb_typeof(source_lineage#>'{observation,supplemental_answer_identity}') = 'string'
                AND length(source_lineage#>>'{observation,supplemental_answer_identity}') > 0
                AND source_lineage#>>'{observation,supplemental_answer_identity}' <> source_input_id
                AND jsonb_typeof(source_lineage#>'{observation,supplemental_answer_version}') = 'string'
                AND length(source_lineage#>>'{observation,supplemental_answer_version}') > 0
                AND source_lineage#>>'{observation,supplemental_answer_bundle_commitment}' ~ '^sha256:[0-9a-f]{64}$'
            ELSE source_lineage#>'{observation,supplemental_answer_identity}' = 'null'::jsonb
                AND source_lineage#>'{observation,supplemental_answer_version}' = 'null'::jsonb
                AND source_lineage#>'{observation,supplemental_answer_bundle_commitment}' = 'null'::jsonb END
        ) IS TRUE),
        CONSTRAINT piece_records_content_shape CHECK ((
            jsonb_typeof(content_payload) = 'object'
            AND content_payload ?& ARRAY['schema_version','meaning_contract_version','safety_contract_version',
                'language','format_type','title','body_blocks']
            AND content_payload - ARRAY['schema_version','meaning_contract_version','safety_contract_version',
                'language','format_type','title','body_blocks'] = '{}'::jsonb
            AND content_payload->>'schema_version' = content_payload_version
            AND content_payload->>'meaning_contract_version' = content_meaning_version
            AND content_payload->>'safety_contract_version' = safety_contract_version
            AND content_payload->>'format_type' = format_type
            AND content_payload->>'language' IN ('ja','en','mixed')
            AND content_payload->'title' = 'null'::jsonb
            AND jsonb_typeof(content_payload->'body_blocks') = 'array'
            AND jsonb_array_length(content_payload->'body_blocks') BETWEEN 1 AND
                CASE WHEN format_type = 'quote' THEN 1 ELSE 3 END
            AND jsonb_typeof(content_payload#>'{body_blocks,0}') = 'string'
            AND length(content_payload#>>'{body_blocks,0}') > 0
            AND (jsonb_array_length(content_payload->'body_blocks') < 2 OR
                (jsonb_typeof(content_payload#>'{body_blocks,1}') = 'string'
                 AND length(content_payload#>>'{body_blocks,1}') > 0))
            AND (jsonb_array_length(content_payload->'body_blocks') < 3 OR
                (jsonb_typeof(content_payload#>'{body_blocks,2}') = 'string'
                 AND length(content_payload#>>'{body_blocks,2}') > 0))
            AND position(chr(13) in piece_text) = 0
            AND piece_text = (content_payload#>>'{body_blocks,0}') ||
                CASE WHEN jsonb_array_length(content_payload->'body_blocks') >= 2 THEN
                    CASE WHEN format_type = 'short_essay' THEN E'\n\n' ELSE E'\n' END ||
                    (content_payload#>>'{body_blocks,1}') ELSE '' END ||
                CASE WHEN jsonb_array_length(content_payload->'body_blocks') >= 3 THEN
                    CASE WHEN format_type = 'short_essay' THEN E'\n\n' ELSE E'\n' END ||
                    (content_payload#>>'{body_blocks,2}') ELSE '' END
        ) IS TRUE),
        CONSTRAINT piece_records_recipe_shape CHECK ((
            jsonb_typeof(visual_recipe) = 'object'
            AND visual_recipe ?& ARRAY['visual_recipe_version','visual_catalog_version','format_type',
                'template','theme','font_style','aspect_ratio','branding','layout_policy_version','language']
            AND visual_recipe - ARRAY['visual_recipe_version','visual_catalog_version','format_type',
                'template','theme','font_style','aspect_ratio','branding','layout_policy_version','language'] = '{}'::jsonb
            AND visual_recipe->>'visual_recipe_version' = visual_recipe_version
            AND visual_recipe->>'visual_catalog_version' = visual_catalog_version
            AND visual_recipe->>'layout_policy_version' = layout_policy_version
            AND visual_recipe->>'format_type' = format_type
            AND visual_recipe->>'language' = content_payload->>'language'
            AND visual_recipe->>'aspect_ratio' IN ('4:5','9:16')
            AND visual_recipe->'template' = jsonb_build_object('template_id',
                CASE format_type WHEN 'short_essay' THEN 'essay_frame'
                    WHEN 'quote' THEN 'focus_frame' ELSE 'stance_frame' END,
                'template_version', 1)
            AND visual_recipe->'theme' IN (
                '{"theme_id":"soft_paper","theme_version":1}'::jsonb,
                '{"theme_id":"quiet_night","theme_version":1}'::jsonb)
            AND visual_recipe->'font_style' =
                '{"font_style_id":"system_readable","font_style_version":1}'::jsonb
            AND visual_recipe->'branding' = jsonb_build_object(
                'branding_mode', visual_recipe#>>'{branding,branding_mode}',
                'branding_mark_id', 'cocolon_text_mark', 'branding_mark_version', 1)
            AND visual_recipe#>>'{branding,branding_mode}' IN ('required_small','required_subtle','off')
            -- Keep the same saved-recipe combinations as B9 validate_visual_recipe.
            -- This neither checks today's tier nor rewrites branding on downgrade.
            AND (visual_recipe#>>'{branding,branding_mode}' <> 'required_small'
                OR (visual_recipe#>>'{theme,theme_id}' = 'soft_paper'
                    AND visual_recipe->>'aspect_ratio' = '4:5'))
        ) IS TRUE)
    );

    CREATE TABLE public.piece_quota_month_locks (
        owner_user_id uuid NOT NULL,
        month_key text NOT NULL CHECK (month_key ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
        created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        PRIMARY KEY (owner_user_id, month_key)
    );
    -- Deliberately NO FK to piece_records: deleting a Piece never refunds quota.
    CREATE TABLE public.piece_quota_consumptions (
        consumption_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_user_id uuid NOT NULL,
        piece_id uuid NOT NULL UNIQUE,
        month_key text NOT NULL CHECK (month_key ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
        subscription_tier_at_consumption text NOT NULL
            CHECK (subscription_tier_at_consumption IN ('free','plus','premium')),
        consumed_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        save_idempotency_key_hash text NOT NULL CHECK (save_idempotency_key_hash ~ '^[0-9a-f]{64}$'),
        reason text NOT NULL DEFAULT 'first_saved_record' CHECK (reason = 'first_saved_record'),
        quota_contract_version text NOT NULL DEFAULT 'piece.quota_consumption.v1'
            CHECK (quota_contract_version = 'piece.quota_consumption.v1'),
        record_contract_version text NOT NULL DEFAULT 'piece.record.v2'
            CHECK (record_contract_version = 'piece.record.v2'),
        UNIQUE (owner_user_id, save_idempotency_key_hash),
        CHECK (month_key = to_char(consumed_at AT TIME ZONE 'Asia/Tokyo', 'YYYY-MM'))
    );
    CREATE TABLE public.piece_record_metrics (
        piece_id uuid PRIMARY KEY REFERENCES public.piece_records(id) ON DELETE CASCADE,
        read_count bigint NOT NULL DEFAULT 0 CHECK (read_count >= 0),
        resonance_count bigint NOT NULL DEFAULT 0 CHECK (resonance_count >= 0),
        updated_at timestamptz NOT NULL DEFAULT transaction_timestamp()
    );
    CREATE TABLE public.piece_record_reads (
        piece_id uuid NOT NULL REFERENCES public.piece_records(id) ON DELETE CASCADE,
        viewer_user_id uuid NOT NULL,
        read_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        PRIMARY KEY (piece_id, viewer_user_id)
    );
    CREATE TABLE public.piece_record_resonances (
        piece_id uuid NOT NULL,
        owner_user_id uuid NOT NULL,
        viewer_user_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        PRIMARY KEY (piece_id, viewer_user_id),
        FOREIGN KEY (piece_id, owner_user_id)
            REFERENCES public.piece_records(id, owner_user_id) ON DELETE CASCADE,
        CHECK (viewer_user_id <> owner_user_id)
    );
    -- Retained, body-free receipts. No record FK or open JSON/metadata payload.
    CREATE TABLE public.piece_export_receipts (
        receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_user_id uuid NOT NULL,
        piece_id uuid NOT NULL,
        idempotency_key_hash text NOT NULL CHECK (idempotency_key_hash ~ '^[0-9a-f]{64}$'),
        piece_text_hash text NOT NULL CHECK (piece_text_hash ~ '^[0-9a-f]{64}$'),
        visual_recipe_hash text NOT NULL CHECK (visual_recipe_hash ~ '^[0-9a-f]{64}$'),
        export_contract_version text NOT NULL DEFAULT 'piece.export_contract.v1'
            CHECK (export_contract_version = 'piece.export_contract.v1'),
        outcome text NOT NULL CHECK (outcome IN ('succeeded','failed')),
        error_code text CHECK (error_code ~ '^PIECE_[A-Z0-9_]{1,80}$'),
        created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        UNIQUE (owner_user_id, idempotency_key_hash),
        CHECK ((outcome = 'succeeded' AND error_code IS NULL)
            OR (outcome = 'failed' AND error_code IS NOT NULL))
    );
    CREATE TABLE public.piece_delete_receipts (
        receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_user_id uuid NOT NULL,
        piece_id uuid NOT NULL,
        idempotency_key_hash text NOT NULL CHECK (idempotency_key_hash ~ '^[0-9a-f]{64}$'),
        record_contract_version text NOT NULL DEFAULT 'piece.record.v2'
            CHECK (record_contract_version = 'piece.record.v2'),
        outcome text NOT NULL CHECK (outcome IN ('succeeded','failed')),
        error_code text CHECK (error_code ~ '^PIECE_[A-Z0-9_]{1,80}$'),
        created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
        UNIQUE (owner_user_id, idempotency_key_hash),
        CHECK ((outcome = 'succeeded' AND error_code IS NULL)
            OR (outcome = 'failed' AND error_code IS NOT NULL))
    );

    CREATE INDEX piece_records_owner_history_idx ON public.piece_records (owner_user_id, saved_at DESC, id)
        WHERE lifecycle_status = 'saved';
    CREATE INDEX piece_records_public_feed_idx ON public.piece_records (saved_at DESC, id)
        WHERE lifecycle_status = 'saved' AND visibility_scope = 'public';
    CREATE INDEX piece_records_source_lookup_idx ON public.piece_records
        (owner_user_id, source_input_id, source_input_version);
    CREATE INDEX piece_records_preview_expiry_idx ON public.piece_records (expires_at, id)
        WHERE lifecycle_status = 'preview_draft';
    CREATE INDEX piece_quota_consumptions_month_idx ON public.piece_quota_consumptions (owner_user_id, month_key);
    CREATE INDEX piece_record_reads_viewer_idx ON public.piece_record_reads (viewer_user_id, read_at DESC);
    CREATE INDEX piece_record_resonances_viewer_idx ON public.piece_record_resonances (viewer_user_id, created_at DESC);
    CREATE INDEX piece_export_receipts_piece_idx ON public.piece_export_receipts (piece_id, created_at DESC);
    CREATE INDEX piece_delete_receipts_piece_idx ON public.piece_delete_receipts (piece_id, created_at DESC);

    FOREACH table_name IN ARRAY targets LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC, anon, authenticated, service_role', table_name);
        -- Remove any other inherited default table ACL, without changing global
        -- defaults or the roles themselves. Later B3 owns all service grants.
        FOR acl_entry IN
            SELECT DISTINCT r.rolname
              FROM pg_catalog.pg_class c
              CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,
                  pg_catalog.acldefault('r', c.relowner))) x
              JOIN pg_catalog.pg_roles r ON r.oid = x.grantee
             WHERE c.oid = pg_catalog.to_regclass('public.' || table_name)
               AND x.grantee <> c.relowner
        LOOP
            EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', table_name, acl_entry.rolname);
        END LOOP;
    END LOOP;
END
$piece_foundation$;
