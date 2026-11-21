-- Keep question payloads stable. The service-only material and issuance RPC
-- bind a selected anchor to an owner source without retaining its literal.
begin;

alter table public.deep_insight_questions add column grounding_receipt jsonb;
grant update (grounding_receipt) on public.deep_insight_questions to service_role;

create or replace function public.deep_insight_material(p_user_id uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
  with profile as (
    select coalesce((select subscription_tier from public.profiles where id=p_user_id),'free') as tier,
      exists(select 1 from public.profiles where id=p_user_id
        and coalesce(subscription_tier,'free') in ('free','plus','premium')) as available
  ), records as (
    select e.id,e.created_at,e.memo as thought,e.memo_action as action,
      encode(sha256(convert_to(public.emlis_parent_source(e)::text,'UTF8')),'hex') as source_version,
      pending.prompt as emlis_open_question,pending.question_id as emlis_open_question_id,
      coalesce(answers.items,'[]'::jsonb) as emlis_answered_questions
    from public.emotions e cross join profile
    left join public.emlis_input_threads t on t.original_emotion_id=e.id and t.user_id=e.user_id
    left join lateral (
      select q.question_id,q.payload->>'prompt_private' as prompt
      from public.emlis_thread_events q
      where t.state='AWAITING_ANSWER' and t.source_snapshot=public.emlis_parent_source(e)
        and coalesce(t.data->>'evaluated_tier',profile.tier)=profile.tier
        and q.thread_id=t.id and q.kind='QUESTION' and q.round_index=t.issued_count
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=q.thread_id
          and v.seq>q.seq and (v.kind='TERMINAL' or v.kind='ANSWER' or
            (v.kind='OPERATION' and (v.payload ? 'question_ending' or
              v.payload->>'stage'='INTERPRETATION_CORRECTION'))))
      order by q.seq desc limit 1
    ) pending on true
    left join lateral (
      select jsonb_agg(jsonb_build_object('id',a.id,'question_id',q.question_id,'answered_at',a.recorded_at,
        'source_version',encode(sha256(convert_to((a.payload->'source')::text,'UTF8')),'hex'),
        'question',q.payload->>'prompt_private','answer',a.payload#>>'{source,answer_text_private}')
        order by q.seq) as items
      from public.emlis_thread_events q join public.emlis_thread_events a
        on a.thread_id=q.thread_id and a.question_id=q.question_id and a.kind='ANSWER'
        and a.round_index=q.round_index and a.seq>q.seq
      where q.thread_id=t.id and q.kind='QUESTION' and t.source_snapshot=public.emlis_parent_source(e)
        and q.payload->>'original_source_ref'=t.data->>'original_source_ref'
        and q.payload->>'prompt_private' ~ '[^[:space:]]'
        and a.payload#>>'{source,answer_id}'=a.id::text
        and a.payload#>>'{source,thread_id}'=t.id::text
        and a.payload#>>'{source,question_id}'=q.question_id
        and a.payload#>>'{source,round_index}'=a.round_index::text
        and a.payload#>>'{source,original_source_ref}'=t.data->>'original_source_ref'
        and a.payload#>>'{source,source_role}'='SUPPLEMENTAL_ANSWER'
        and a.payload#>>'{source,source_version}'='cocolon.cmee.supplemental_answer.v1'
        and a.payload#>>'{source,answer_text_private}' ~ '[^[:space:]]'
        -- Multi-answer and corrected threads need the Emlis effective-meaning
        -- reader. Never put an unqualified historical answer back into a prompt.
        and not exists (select 1 from public.emlis_thread_events v where v.thread_id=t.id
          and ((v.kind='ANSWER' and v.id<>a.id) or
            (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION')))
    ) answers on true
    where e.user_id=p_user_id and public.emlis_parent_visible(e.created_at,profile.tier,statement_timestamp())
      and (e.memo ~ '[^[:space:]]' or e.memo_action ~ '[^[:space:]]' or answers.items is not null)
      and coalesce(t.data->>'body_state','') <> 'SAFETY'
    order by e.created_at desc,e.id limit 8
  ), prior as (
    select q.id,q.lane,q.theme,q.question_text,q.answer_text,q.answered_at,q.issued_at,q.question_key,q.text_key,
      q.grounding_receipt,
      case when q.answered_at is not null then encode(sha256(convert_to(jsonb_build_array(
        q.id,q.question_text,q.answer_text,q.answered_at)::text,'UTF8')),'hex') end as source_version
    from public.deep_insight_questions q where q.user_id=p_user_id
    order by q.issued_at desc,q.id limit 30
  ), map_guard as materialized (
    select case when profile.available and exists(select 1 from public.analysis_observed_artifacts
      where user_id=p_user_id and source_profile='cumulative.v1')
      then public.analysis_cumulative_source_snapshot(p_user_id)->>'guard' end as value
    from profile
  ), map as (
    select jsonb_build_object('id',a.id,'generated_at',a.generated_at,
      'source_version',encode(sha256(convert_to(a.source_guard,'UTF8')),'hex'),
      'summary',left(a.content_text,1800)) as item
    from public.analysis_observed_artifacts a cross join map_guard
    where a.user_id=p_user_id and a.source_profile='cumulative.v1'
      and a.source_guard=map_guard.value
    order by a.generated_at desc,a.id desc limit 1
  )
  select jsonb_build_object(
    'records',coalesce((select jsonb_agg(to_jsonb(r) order by r.created_at desc,r.id) from records r),'[]'::jsonb),
    'prior',coalesce((select jsonb_agg(to_jsonb(p) order by p.issued_at desc,p.id) from prior p),'[]'::jsonb),
    'map',(select item from map));
$$;

create function public.deep_insight_issue_grounded(p_user_id uuid,p_day date,p_lane text,p_theme text,
  p_question_text text,p_question_key text,p_text_key text,p_material_guard text,p_grounding_receipt jsonb)
returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  receipt jsonb:=p_grounding_receipt;
  shape constant text[]:=array['policy_version','lane','focus','source_id','source_version','field',
    'start','end','literal_sha256','condition_key','target_key'];
  source_id text; source_version text; field text; original text;
  start_at integer; end_at integer;
  material jsonb; result jsonb;
begin
  if p_lane is null or p_lane not in ('records','theme')
    or jsonb_typeof(receipt) is distinct from 'object' or octet_length(receipt::text)>1536
    or not receipt ?& shape or receipt-shape<>'{}'::jsonb
    or receipt->>'policy_version' is distinct from 'deep-insight.v2'
    or receipt->>'lane' is distinct from p_lane
    or coalesce(receipt->>'focus','') not in ('REASON','CONDITION','VALUE','CHANGE','RELATIONSHIP','PREFERENCE','MEANING')
    or coalesce(receipt->>'target_key','') !~ '^[0-9a-f]{64}$'
    or (receipt->'condition_key'<>'null'::jsonb and coalesce(receipt->>'condition_key','') !~ '^[0-9a-f]{64}$')
    or p_question_key is distinct from 'deep-insight-target-' || (receipt->>'target_key') then
    raise sqlstate '22023' using message='deep_insight_grounding_invalid';
  end if;

  if p_lane='theme' then
    if receipt->'source_id'<>'null'::jsonb or receipt->'source_version'<>'null'::jsonb
      or receipt->'field'<>'null'::jsonb or receipt->'start'<>'null'::jsonb
      or receipt->'end'<>'null'::jsonb or receipt->'literal_sha256'<>'null'::jsonb then
      raise sqlstate '22023' using message='deep_insight_grounding_invalid';
    end if;
  else
    source_id:=receipt->>'source_id';
    source_version:=receipt->>'source_version';
    field:=receipt->>'field';
    if coalesce(source_id,'') !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
      or coalesce(source_version,'') !~ '^[0-9a-f]{64}$' or coalesce(field,'') not in ('thought','action','answer')
      or coalesce(receipt->>'literal_sha256','') !~ '^[0-9a-f]{64}$'
      or jsonb_typeof(receipt->'start') is distinct from 'number' or jsonb_typeof(receipt->'end') is distinct from 'number'
      or coalesce(receipt->>'start','') !~ '^(0|[1-9][0-9]{0,7})$'
      or coalesce(receipt->>'end','') !~ '^[1-9][0-9]{0,7}$' then
      raise sqlstate '22023' using message='deep_insight_grounding_invalid';
    end if;
    start_at:=(receipt->>'start')::integer;
    end_at:=(receipt->>'end')::integer;
    if start_at>=end_at then raise sqlstate '22023' using message='deep_insight_grounding_invalid'; end if;

    material:=public.deep_insight_material(p_user_id);
    if encode(sha256(convert_to(material::text,'UTF8')),'hex') is distinct from p_material_guard then
      return jsonb_build_object('status','no_question','question',null);
    end if;
    if field='answer' then
      select text into original from (
        select row->>'id' as id,row->>'source_version' as version,row->>'answer_text' as text
        from jsonb_array_elements(material->'prior') row
        union all
        select source->>'id',source->>'source_version',source->>'answer'
        from jsonb_array_elements(material->'records') row
        cross join lateral jsonb_array_elements(row->'emlis_answered_questions') source
      ) sources where id=source_id and version=source_version limit 1;
    else
      select row->>field into original from jsonb_array_elements(material->'records') row
      where row->>'id'=source_id and row->>'source_version'=source_version limit 1;
    end if;
    if original is null or end_at>char_length(original) or
      encode(sha256(convert_to(substr(original,start_at+1,end_at-start_at),'UTF8')),'hex')
        is distinct from receipt->>'literal_sha256' then
      raise sqlstate '22023' using message='deep_insight_grounding_invalid';
    end if;
  end if;

  result:=public.deep_insight_issue(p_user_id,p_day,p_lane,p_theme,p_question_text,p_question_key,
    p_text_key,p_material_guard);
  if result->>'status'='issued' then
    update public.deep_insight_questions set grounding_receipt=receipt
    where id=(result#>>'{question,id}')::uuid and user_id=p_user_id and grounding_receipt is null;
    if not found then raise sqlstate '40001' using message='deep_insight_grounding_write_conflict'; end if;
  end if;
  return result;
end;
$$;

revoke all on function public.deep_insight_issue_grounded(uuid,date,text,text,text,text,text,text,jsonb)
  from public,anon,authenticated;
grant execute on function public.deep_insight_issue_grounded(uuid,date,text,text,text,text,text,text,jsonb)
  to service_role;

commit;
