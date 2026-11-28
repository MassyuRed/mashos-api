begin;

-- A current Map read includes the new entry in its live cohort. Emlis needs
-- the eligible saved version from before that entry, using the same cohort
-- reauthorization as saved if-route material.
create function public.emlis_thread_prior_map_context(p_user_id uuid,p_input_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  with candidate as materialized (
    select a.id,a.artifact_version,a.generated_at,a.period_end,a.safe_projection,
      a.private_evidence->'source_record_refs' as refs,
      coalesce(a.cumulative_source_guard,a.source_guard) as source_guard
    from public.emotions parent
    join public.profiles p on p.id=parent.user_id and p.subscription_tier='premium'
    join public.analysis_observed_artifacts a on a.user_id=parent.user_id
    where parent.id=p_input_id and parent.user_id=p_user_id
      and a.source_profile='cumulative.v1'
      and a.generated_at < parent.created_at at time zone 'UTC'
      and a.period_end <= parent.created_at at time zone 'UTC'
      and a.safe_projection->>'wire_kind'='watashi.map.v3'
      and public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence)
      and jsonb_typeof(a.safe_projection#>'{overview,primary_structures}')='array'
      and jsonb_typeof(a.private_evidence->'source_record_refs')='array'
      and a.private_evidence->'source_record_refs'<>'[]'::jsonb
      and not (a.private_evidence->'source_record_refs' ? p_input_id::text)
    order by a.generated_at desc,a.id desc limit 1
  ), admitted as materialized (
    select c.* from candidate c
    where public.analysis_if_sources_current(p_user_id,c.source_guard,c.refs)
  )
  select jsonb_build_object('ref', jsonb_build_object(
      'id',a.id,'version',a.artifact_version,'guard',a.source_guard,'period_end',a.period_end,
      'visibility',encode(sha256(convert_to(coalesce((
        select jsonb_agg(jsonb_build_array(e.id,e.is_secret) order by e.id)
        from public.emotions e where e.user_id=p_user_id and a.refs ? e.id::text
      ),'[]'::jsonb)::text,'UTF8')),'hex')),
    'generated_at',a.generated_at,'structures',sections.items)
  from admitted a
  cross join lateral (
    select jsonb_agg(jsonb_build_object('title',section->>'title',
      'description',section->>'description') order by ord) as items
    from jsonb_array_elements(a.safe_projection#>'{overview,primary_structures}')
      with ordinality as x(section,ord)
    where ord<=3 and nullif(btrim(section->>'title'),'') is not null
      and nullif(btrim(section->>'description'),'') is not null
      and char_length(section->>'title')<=150 and char_length(section->>'description')<=1200
  ) sections
  where sections.items is not null;
$$;

-- A completed Emlis reply can outlive the derived Map cache. Reconstruct the
-- original cohort from its saved cutoff and validate the saved source digest.
create function public.emlis_thread_prior_map_is_current(p_user_id uuid,p_input_id uuid,
  p_map_id uuid,p_period_end timestamptz,p_guard text,p_visibility text)
returns boolean language sql stable security invoker set search_path='' as $$
  with permitted as materialized (
    select public.analysis_cumulative_source_snapshot(p_user_id)->'members' as members
    from public.emotions parent
    join public.profiles p on p.id=parent.user_id and p.subscription_tier='premium'
    where parent.id=p_input_id and parent.user_id=p_user_id
      and p_period_end<=parent.created_at at time zone 'UTC'
      and not exists(select 1 from public.analysis_observed_artifacts a
        where a.id=p_map_id and a.user_id=p_user_id
          and not public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence))
  ), pinned as materialized (
    select coalesce(jsonb_agg(m#>>'{original,id}'),'[]'::jsonb) as refs
    from permitted p cross join lateral jsonb_array_elements(p.members) m
    where (case when m ? 'deep_insight' then (m#>>'{original,created_at}')::timestamptz
                else (m#>>'{original,created_at}')::timestamp at time zone 'UTC' end)<p_period_end
  )
  select coalesce((select refs<>'[]'::jsonb
    and public.analysis_if_sources_current(p_user_id,p_guard,refs)
    and p_visibility=encode(sha256(convert_to(coalesce((
      select jsonb_agg(jsonb_build_array(e.id,e.is_secret) order by e.id)
      from public.emotions e where e.user_id=p_user_id and refs ? e.id::text
    ),'[]'::jsonb)::text,'UTF8')),'hex') from pinned),false);
$$;

revoke all on function public.emlis_thread_prior_map_context(uuid,uuid)
  from public,anon,authenticated,service_role;
grant execute on function public.emlis_thread_prior_map_context(uuid,uuid) to service_role;
revoke all on function public.emlis_thread_prior_map_is_current(uuid,uuid,uuid,timestamptz,text,text)
  from public,anon,authenticated,service_role;
grant execute on function public.emlis_thread_prior_map_is_current(uuid,uuid,uuid,timestamptz,text,text) to service_role;

commit;
