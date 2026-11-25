-- Expose only the safe view from the same saved artifact, using the same viewer-tier read.
create or replace function public.analysis_cumulative_read(p_user_id uuid,p_id uuid default null,
  p_history boolean default false,p_limit integer default 60,p_offset integer default 0,
  p_month date default null,p_metadata_only boolean default false)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare snap jsonb; tier text; max_months integer; current_id uuid; items jsonb;
begin
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  if not found or tier not in ('free','plus','premium') then
    raise sqlstate '42501' using message='analysis_owner_unavailable'; end if;
  max_months:=case tier when 'free' then 2 when 'plus' then 12 else null end;
  if p_limit not between 1 and 200 or p_offset not between 0 and 10000 then
    raise sqlstate '22023' using message='analysis_page_invalid'; end if;
  if not p_history and p_month is null then
    snap:=public.analysis_cumulative_source_snapshot(p_user_id);
    current_id:=public.analysis_cumulative_current_id(p_user_id,snap->>'guard');
  end if;
  with ranked as (
    select m.*,row_number() over(order by snapshot_month desc) as n
      from public.analysis_cumulative_months m where m.user_id=p_user_id
  ), visible as (
    select r.artifact_id as id,r.snapshot_month,r.captured_at,'monthly'::text as kind
      from ranked r where (max_months is null or r.n<=max_months)
      and (p_month is null or r.snapshot_month=p_month)
      and (p_history or p_id is not null)
    union all
    select current_id,null::date,null::timestamptz,'latest'::text
      where current_id is not null and not p_history and p_month is null
  ), page as (
    select a.*,v.snapshot_month,v.captured_at,v.kind
    from visible v join public.analysis_observed_artifacts a on a.id=v.id and a.user_id=p_user_id
    where (p_id is null or a.id=p_id)
    order by v.snapshot_month desc nulls last,a.generated_at desc,a.id desc
    limit p_limit offset p_offset
  ) select coalesce(jsonb_agg(jsonb_build_object('id',id,'report_type',kind,
    'report_mode','standard','title','わたしマップ','period_start',period_start,'period_end',period_end,
    'generated_at',generated_at,'updated_at',generated_at,'snapshot_month',snapshot_month,
    'captured_at',captured_at,'source_profile','cumulative.v1') ||
    case when p_metadata_only then '{}'::jsonb else jsonb_build_object('content_text',content_text,
      'content_json',jsonb_build_object('report_mode','standard','watashiMap',safe_projection,
      'map_context',private_evidence->'coverage') ||
      case when tier='premium' and safe_projection->>'wire_kind'='watashi.map.v3'
          and private_evidence->>'projection_of'=safe_projection->>'projection_of'
          and jsonb_typeof(private_evidence #> '{graph,meaning_review,structure_relations,views}')='array'
        then jsonb_build_object('structure_relations',
          private_evidence #> '{graph,meaning_review,structure_relations,views}')
        else '{}'::jsonb end) end
    order by snapshot_month desc nulls last,generated_at desc,id desc),'[]'::jsonb) into items from page;
  return jsonb_build_object('items',items,'subscription_tier',tier,'matched',
    exists(select 1 from public.analysis_observed_artifacts where user_id=p_user_id
      and source_profile='cumulative.v1' and id=p_id),'history_limit',max_months);
end;
$$;
