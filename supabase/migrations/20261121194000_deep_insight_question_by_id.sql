begin;

create function public.deep_insight_question_by_id(p_user_id uuid,p_question_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare
  question jsonb;
begin
  select public.deep_insight_question_payload(q) into question
  from public.deep_insight_questions q
  where q.user_id=p_user_id and q.id=p_question_id;
  if not found then
    raise sqlstate 'P0002' using message='deep_insight_question_unavailable';
  end if;
  return question;
end;
$$;

revoke all on function public.deep_insight_question_by_id(uuid,uuid) from public,anon,authenticated;
grant execute on function public.deep_insight_question_by_id(uuid,uuid) to service_role;

commit;
