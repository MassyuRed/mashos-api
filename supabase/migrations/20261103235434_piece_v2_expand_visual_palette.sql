-- Add themes to the existing recipe shape. Existing rows and recipe hashes
-- keep their original bytes. Preview and save RPCs still own all row and quota
-- transitions. No change to roles, privileges, or RLS.
ALTER TABLE public.piece_records
    DROP CONSTRAINT piece_records_recipe_shape,
    ADD CONSTRAINT piece_records_recipe_shape CHECK ((
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
                '{"theme_id":"quiet_night","theme_version":1}'::jsonb,
                '{"theme_id":"rose_paper","theme_version":1}'::jsonb,
                '{"theme_id":"rose_berry","theme_version":1}'::jsonb,
                '{"theme_id":"sand_umber","theme_version":1}'::jsonb,
                '{"theme_id":"sand_olive","theme_version":1}'::jsonb,
                '{"theme_id":"mist_slate","theme_version":1}'::jsonb,
                '{"theme_id":"mist_teal","theme_version":1}'::jsonb,
                '{"theme_id":"lavender_ink","theme_version":1}'::jsonb,
                '{"theme_id":"lavender_plum","theme_version":1}'::jsonb,
                '{"theme_id":"forest_mint","theme_version":1}'::jsonb,
                '{"theme_id":"ocean_ice","theme_version":1}'::jsonb)
            AND visual_recipe->'font_style' =
                '{"font_style_id":"system_readable","font_style_version":1}'::jsonb
            AND visual_recipe->'branding' = jsonb_build_object(
                'branding_mode', visual_recipe#>>'{branding,branding_mode}',
                'branding_mark_id', 'cocolon_text_mark', 'branding_mark_version', 1)
            AND visual_recipe#>>'{branding,branding_mode}' IN ('required_small','required_subtle','off')
            -- Keep the same saved-recipe combinations as B9 validate_visual_recipe.
            -- This neither checks today's tier nor rewrites branding on downgrade.
            AND (visual_recipe#>>'{branding,branding_mode}' <> 'required_small'
                OR (visual_recipe#>>'{theme,theme_id}' IN ('soft_paper','quiet_night')
                    AND visual_recipe->>'aspect_ratio' = '4:5'))
        ) IS TRUE);
