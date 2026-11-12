-- Capture this input's question choice in the same INSERT as the emotion.
-- It is a delivery preference, never an original-meaning/source field.
begin;

alter table public.emotions
  add column receive_emlis_questions boolean not null default true;

comment on column public.emotions.receive_emlis_questions is
  'Question receiving choice captured for this input; unrelated to history access or emotion notifications.';

-- Preserve the existing source keys, ownership/liveness filters, INVOKER and
-- function identity/ACL. Only the private snapshot sibling is additive.
create or replace function public.emlis_thread_read(p_user_id uuid,p_input_id uuid default null,p_thread_id uuid default null)
returns jsonb language sql volatile security invoker set search_path='' as $$
  select jsonb_build_object('original',public.emlis_parent_source(e),
    'receive_emlis_questions',e.receive_emlis_questions,
    'tier',coalesce(p.subscription_tier,'free'),'now',statement_timestamp(),
    'thread',case when t.id is null then null else to_jsonb(t) end,
    'events',coalesce((select jsonb_agg(to_jsonb(v) order by v.seq)
      from public.emlis_thread_events v where v.thread_id=t.id),'[]'::jsonb))
  from public.emotions e left join public.profiles p on p.id=e.user_id
  left join public.emlis_input_threads t on t.original_emotion_id=e.id
  where e.user_id=p_user_id and (t.id is null or t.user_id=p_user_id)
    and ((p_input_id is not null and e.id=p_input_id and p_thread_id is null)
    or (p_thread_id is not null and t.id=p_thread_id and p_input_id is null))
    and public.emlis_parent_visible(e.created_at,coalesce(p.subscription_tier,'free'),statement_timestamp());
$$;

commit;
