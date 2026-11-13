-- Carry only user-authored correction sources into entitled natural history.
-- Search all entitled prior records; the model still receives at most 3/6.
-- Saved replies reread their exact selected IDs rather than searching again.
begin;
create or replace function public.emlis_thread_related_context(
  p_user_id uuid,p_input_id uuid,p_context_guards jsonb default null
) returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  parent public.emotions; current_thread public.emlis_input_threads;
  tier text; instant timestamptz := statement_timestamp(); selected_limit integer;
  focus text; history jsonb; feedback jsonb;
begin
  select * into parent from public.emotions where id=p_input_id and user_id=p_user_id;
  if not found then raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  select coalesce(subscription_tier,'free') into tier from public.profiles where id=p_user_id;
  tier := coalesce(tier,'free');
  if not public.emlis_parent_visible(parent.created_at,tier,instant) then
    raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  select * into current_thread from public.emlis_input_threads where original_emotion_id=p_input_id;
  if current_thread.id is not null and current_thread.user_id<>p_user_id then
    raise sqlstate 'P0002' using message='emlis_parent_unavailable'; end if;
  selected_limit := case tier when 'premium' then 6 when 'plus' then 3 else 0 end;
  if p_context_guards is not null then
    if jsonb_typeof(p_context_guards) is distinct from 'array' then
      raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
    if jsonb_array_length(p_context_guards)>6 or exists(
      select 1 from jsonb_array_elements(p_context_guards) g
      where case when jsonb_typeof(g)<>'array' then true else jsonb_array_length(g)<>3 end
    ) then raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
    if exists(select 1 from jsonb_array_elements(p_context_guards) g
      where jsonb_typeof(g->0)<>'string' or jsonb_typeof(g->1)<>'string'
        or jsonb_typeof(g->2)<>'number' or coalesce(g->>1,'') !~ '^[0-9a-f]{32}$'
        or coalesce(g->>2,'') !~ '^[0-9]+$') then
      raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
    if (select count(distinct (g->>0)::uuid) from jsonb_array_elements(p_context_guards) g)
      <> jsonb_array_length(p_context_guards) then
      raise sqlstate '22023' using message='emlis_context_guards_invalid'; end if;
  end if;
  if selected_limit=0 then
    return jsonb_build_object('history','[]'::jsonb,'feedback','[]'::jsonb); end if;
  select concat_ws(E'\n',parent.memo,parent.memo_action,
    (select string_agg(v.payload->'source'->>'answer_text_private',E'\n' order by v.seq)
      from public.emlis_thread_events v where v.thread_id=current_thread.id and v.kind='ANSWER'),
    (select string_agg(v.payload->'source'->>'explanation',E'\n' order by v.seq)
      from public.emlis_thread_events v where v.thread_id=current_thread.id
        and v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'),
    (select string_agg(f.correction_text,E'\n' order by f.updated_at,f.frame_key)
      from public.emlis_frame_feedback f where f.user_id=p_user_id
        and f.source_emotion_id=parent.id and f.status='REVISED')) into focus;
  with segments as (
    select (regexp_matches(lower(coalesce(focus,'')), '[0-9a-z一-龯ぁ-んァ-ヶー]+','g'))[1] segment
  ), terms as (
    select distinct substring(s.segment from g.n for 3) term from segments s
      cross join lateral generate_series(1,char_length(s.segment)-2) g(n)
    union select segment from segments where char_length(segment)=2
  ), eligible as (
    select h.id,h.created_at,lower(concat_ws(E'\n',h.memo,h.memo_action,
      (select string_agg(v.payload->'source'->>'answer_text_private',E'\n' order by v.seq)
        from public.emlis_thread_events v where v.thread_id=ht.id and v.kind='ANSWER'),
    (select string_agg(v.payload->'source'->>'explanation',E'\n' order by v.seq)
      from public.emlis_thread_events v where v.thread_id=ht.id
        and v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'),
      (select string_agg(f.correction_text,E'\n' order by f.updated_at,f.frame_key)
        from public.emlis_frame_feedback f where f.user_id=p_user_id
          and f.source_emotion_id=h.id and f.status='REVISED'))) search_text
    from public.emotions h left join public.emlis_input_threads ht on ht.original_emotion_id=h.id
    where h.user_id=p_user_id and (ht.id is null or ht.user_id=p_user_id)
      and (ht.id is null or ht.source_snapshot=public.emlis_parent_source(h))
      and (h.created_at,h.id)<(parent.created_at,parent.id)
      and public.emlis_parent_visible(h.created_at,tier,instant)
      and (p_context_guards is null or h.id in
        (select (g->>0)::uuid from jsonb_array_elements(p_context_guards) g))
  ), ranked as (
    select e.id,e.created_at,case when p_context_guards is not null then 1
      else (select count(*) from terms q where strpos(e.search_text,q.term)>0) end score from eligible e
  ), chosen as (
    select * from ranked where p_context_guards is not null or score>0
    order by score desc,created_at desc,id limit selected_limit
  )
  select coalesce(jsonb_agg(x.payload order by x.created_at,x.id),'[]'::jsonb) into history from (
    select h.id,h.created_at,jsonb_build_object('original',public.emlis_parent_source(h),
      'thread',case when ht.id is null then null else to_jsonb(ht)-'source_snapshot' end,
      'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq) from public.emlis_thread_events v
        where v.thread_id=ht.id and (v.kind in ('QUESTION','ANSWER') or (v.kind='OPERATION' and v.payload->>'stage'='INTERPRETATION_CORRECTION'))),'[]'::jsonb),
      'guard',jsonb_build_array(h.id,md5(public.emlis_parent_source(h)::text),coalesce(ht.revision,0))) payload
    from chosen c join public.emotions h on h.id=c.id
      left join public.emlis_input_threads ht on ht.original_emotion_id=h.id
  ) x;
  select coalesce(jsonb_agg(to_jsonb(f) order by f.frame_key),'[]'::jsonb) into feedback
    from public.emlis_frame_feedback f where f.user_id=p_user_id and tier='premium'
      and (f.source_emotion_id=parent.id or f.source_emotion_id in
        (select (h->'original'->>'id')::uuid from jsonb_array_elements(history) h));
  return jsonb_build_object('history',history,'feedback',feedback);
end;
$$;
revoke all on function public.emlis_thread_related_context(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.emlis_thread_related_context(uuid,uuid,jsonb) to service_role;

commit;
