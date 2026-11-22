-- Admit the relational 4B map alongside immutable historical v2 maps.
-- Only the paired wire/private schema checks change. Owner identity, source
-- guards, retention, size policy, RLS, ACL and existing rows remain unchanged.
begin;

alter table public.analysis_observed_artifacts
  drop constraint analysis_observed_artifacts_private_evidence_check,
  add constraint analysis_observed_artifacts_private_evidence_check check (
    (jsonb_typeof(private_evidence)='object'
      and private_evidence->>'schema_version' in (
        'analysis.private-evidence.v1','analysis.private-evidence.v2',
        'analysis.semantic-private-evidence.v1')
      and private_evidence->>'projection_of'=artifact_id || '@' || artifact_version::text) is true),
  drop constraint analysis_observed_artifacts_check3,
  add constraint analysis_observed_artifacts_check3 check (
    (jsonb_typeof(safe_projection)='object'
      and safe_projection->>'projection_of'=artifact_id || '@' || artifact_version::text
      and (
        (safe_projection->>'wire_kind'='watashi.map.v2'
          and private_evidence->>'schema_version' in (
            'analysis.private-evidence.v1','analysis.private-evidence.v2'))
        or
        (safe_projection->>'wire_kind'='watashi.map.v3'
          and safe_projection->>'schema_version'='cocolon.analysis.semantic_map.v1'
          and safe_projection->'artifact_version'=to_jsonb(artifact_version)
          and private_evidence->>'schema_version'='analysis.semantic-private-evidence.v1'
          and source_profile='cumulative.v1'
          and safe_projection ?& array['schema_version','wire_kind','projection_of',
            'artifact_version','period_label','overview','nodes','edges','accessibility_linear_order']
          and safe_projection - array['schema_version','wire_kind','projection_of',
            'artifact_version','period_label','overview','nodes','edges','accessibility_linear_order']='{}'::jsonb
          and jsonb_typeof(safe_projection->'overview')='object'
          and jsonb_typeof(safe_projection->'nodes')='array'
          and jsonb_typeof(safe_projection->'edges')='array'
          and jsonb_typeof(safe_projection->'accessibility_linear_order')='array')
      )) is true);

commit;
