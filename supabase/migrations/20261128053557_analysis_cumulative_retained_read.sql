begin;

create function public.analysis_cumulative_retained_read(p_user_id uuid,p_metadata_only boolean default false)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; prior public.analysis_observed_artifacts; tier text; history_limit integer; item jsonb;
begin
  snap:=public.analysis_cumulative_source_snapshot(p_user_id);
  tier:=snap->>'tier';
  history_limit:=case tier when 'free' then 2 when 'plus' then 12 else null end;
  if public.analysis_cumulative_current_id(p_user_id,snap->>'guard') is null then
    -- A retained read uses the earlier version only when every source from
    -- that version still has the same content and correction state today.
    select a.* into prior
    from public.analysis_observed_artifacts a
    cross join lateral (
      select jsonb_agg(m order by ord) as members,count(*) as size
      from jsonb_array_elements(snap->'members') with ordinality as source(m,ord)
      where a.private_evidence->'source_record_refs' ? (m#>>'{original,id}')
    ) as cohort
    cross join lateral (
      select public.analysis_cumulative_material_guard(p_user_id,
        jsonb_set(snap,'{members}',coalesce(cohort.members,'[]'::jsonb))) as guard
    ) as current_cohort
    where a.user_id=p_user_id and a.source_profile='cumulative.v1'
      and jsonb_typeof(a.private_evidence->'source_record_refs')='array'
      and cohort.size>0
      and cohort.size=jsonb_array_length(a.private_evidence->'source_record_refs')
      and (a.source_guard=current_cohort.guard or a.cumulative_source_guard=current_cohort.guard)
      and public.analysis_cumulative_has_accepted_reading(a.safe_projection,a.private_evidence)
    order by a.generated_at desc,a.id desc limit 1;
  end if;

  if prior.id is not null then
    item:=jsonb_build_object('id',prior.id,'report_type','latest','report_mode','standard',
      'title','わたしマップ','period_start',prior.period_start,'period_end',prior.period_end,
      'generated_at',prior.generated_at,'updated_at',prior.generated_at,'snapshot_month',null,
      'captured_at',null,'source_profile','cumulative.v1');
    if not p_metadata_only then
      item:=item || jsonb_build_object('content_text',prior.content_text,
        'content_json',jsonb_build_object('report_mode','standard','watashiMap',prior.safe_projection,
          'map_context',prior.private_evidence->'coverage') || case when tier='premium'
            and prior.safe_projection->>'wire_kind'='watashi.map.v3'
            and prior.private_evidence->>'projection_of'=prior.safe_projection->>'projection_of'
            and jsonb_typeof(prior.private_evidence#>'{graph,meaning_review,structure_relations,views}')='array'
            then jsonb_build_object('structure_relations',prior.private_evidence#>'{graph,meaning_review,structure_relations,views}')
            else '{}'::jsonb end);
    end if;
  end if;
  return jsonb_build_object('items',case when item is null then '[]'::jsonb else jsonb_build_array(item) end,
    'subscription_tier',tier,'matched',prior.id is not null,'history_limit',history_limit);
end;
$$;

revoke all on function public.analysis_cumulative_retained_read(uuid,boolean) from public,anon,authenticated;
grant execute on function public.analysis_cumulative_retained_read(uuid,boolean) to service_role;

commit;
