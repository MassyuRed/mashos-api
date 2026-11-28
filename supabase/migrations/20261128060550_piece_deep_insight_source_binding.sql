begin;

-- Private draft-source proof for an explicitly selected DeepInsight answer.
-- When called inside a write, the locks hold the selected sources to commit.
-- The existing Piece operations do not register this candidate source yet.
create function public.piece_deep_insight_source_binding(
  p_owner uuid, p_saved_input uuid, p_question uuid, p_expected_commitment text default null
) returns jsonb language plpgsql volatile security invoker set search_path='' as $$
declare
  parent public.emotions;
  thread public.emlis_input_threads;
  question public.deep_insight_questions;
  tier text;
  original jsonb;
  receipt jsonb;
  field_text text;
  range_start integer;
  range_end integer;
  commitment text;
  as_of timestamptz := clock_timestamp();
begin
  select e.* into parent from public.emotions e
    where e.id=p_saved_input and e.user_id=p_owner for share;
  if not found or parent.is_secret is not false then return null; end if;
  select p.subscription_tier into tier from public.profiles p where p.id=p_owner for share;
  as_of:=clock_timestamp();
  if not found or tier not in ('free','plus','premium') or tier is null
    or parent.created_at at time zone 'UTC'>=as_of
    or public.emlis_parent_visible(parent.created_at,tier,as_of) is not true then return null; end if;

  original:=public.emlis_parent_source(parent);
  select t.* into thread from public.emlis_input_threads t where t.original_emotion_id=p_saved_input for share;
  if found and (thread.user_id is distinct from p_owner or thread.source_snapshot is distinct from original
    or thread.data->>'body_state'='SAFETY'
    or exists(select 1 from public.emlis_thread_events e where e.thread_id=thread.id and e.kind='OPERATION'
      and e.payload->>'stage'='INTERPRETATION_CORRECTION')
    or (select count(*) from public.emlis_thread_events e where e.thread_id=thread.id and e.kind='ANSWER')>=2)
    then return null; end if;

  select q.* into question from public.deep_insight_questions q
    where q.id=p_question and q.user_id=p_owner and q.lane='records' for share;
  if not found or question.answer_text is null or question.answered_at is null
    or question.issued_at<parent.created_at at time zone 'UTC' or question.answered_at<question.issued_at
    or question.answered_at>=as_of then return null; end if;

  receipt:=question.grounding_receipt;
  if receipt->>'policy_version' is distinct from 'deep-insight.v2'
    or receipt->>'lane' is distinct from 'records'
    or receipt->>'source_id' is distinct from p_saved_input::text
    or receipt->>'source_version' is distinct from encode(sha256(convert_to(original::text,'UTF8')),'hex')
    or question.question_key is distinct from 'deep-insight-target-'||(receipt->>'target_key')
    or jsonb_typeof(receipt->'start') is distinct from 'number'
    or jsonb_typeof(receipt->'end') is distinct from 'number'
    or coalesce(receipt->>'start','') !~ '^[0-9]{1,8}$'
    or coalesce(receipt->>'end','') !~ '^[0-9]{1,8}$' then return null; end if;
  field_text:=case receipt->>'field' when 'thought' then parent.memo when 'action' then parent.memo_action end;
  range_start:=(receipt->>'start')::integer;
  range_end:=(receipt->>'end')::integer;
  if field_text is null or range_end-range_start not between 6 and 70 or range_end>char_length(field_text)
    or receipt->>'literal_sha256' is distinct from encode(sha256(convert_to(
      substr(field_text,range_start+1,range_end-range_start),'UTF8')),'hex') then return null; end if;

  commitment:='sha256:'||encode(sha256(convert_to(jsonb_build_array('piece.deep_insight_answer.v1',
    p_owner,p_saved_input,p_question,original,receipt,question.issued_at,question.answered_at,
    question.question_text,question.answer_text,thread.id,thread.revision)::text,'UTF8')),'hex');
  if p_expected_commitment is not null and p_expected_commitment<>commitment then return null; end if;
  return jsonb_build_object('source_version','piece.deep_insight_answer.v1','commitment',commitment,
    'subscription_tier',tier,'original',original,'answer_id',question.id,'answer_text',question.answer_text,
    'answered_at',question.answered_at,'ai_question_context',question.question_text);
end;
$$;

revoke all on function public.piece_deep_insight_source_binding(uuid,uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.piece_deep_insight_source_binding(uuid,uuid,uuid,text) to service_role;

commit;
