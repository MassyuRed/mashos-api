begin;

create function public.analysis_cumulative_completion_push()
returns trigger language plpgsql security invoker set search_path='' as $$
declare
  event constant text := 'watashi_map_updated';
  title constant text := 'Emlis';
  body constant text := 'わたしマップが更新されました';
  owner_id text := new.user_id::text;
  report_id text := new.id::text;
  version_key text := 'artifact:' || replace(report_id,'-','') || '@1';
  prefix text;
  digest text;
  payload_data jsonb;
begin
  if not public.analysis_cumulative_has_accepted_reading(new.safe_projection,new.private_evidence)
      or new.safe_projection->>'projection_of' is distinct from version_key then
    return null;
  end if;

  -- Match the same deterministic key used by deployed Python writers so
  -- their post-commit reservation is harmless during rolling deployment.
  prefix := left(encode(sha256(convert_to(event || ':' || report_id,'UTF8')),'hex'),24);
  digest := left(encode(sha256(convert_to(format(
    '{"actor_user_id":"%s","body":"%s","chunk_index":0,"data":{"report_id":"%s","screen":"Analysis","target":"watashi_map","type":"%s","user_id":"%s","version_key":"%s"},"event_type":"%s","prefix":"%s","recipient_user_ids":["%s"],"title":"%s"}',
    owner_id,body,report_id,event,owner_id,version_key,event,prefix,owner_id,title),'UTF8')),'hex'),24);
  payload_data := jsonb_build_object('type',event,'target','watashi_map','screen','Analysis',
    'user_id',owner_id,'report_id',report_id,'version_key',version_key);

  insert into public.astor_jobs(job_key,job_type,user_id,payload,priority,run_after,max_attempts)
  values('fcm_push:' || event || ':' || prefix || ':0:' || digest,'send_fcm_push_v1',new.user_id,
    jsonb_build_object('schema_version','fcm.push.job.v1','recipient_mode','user_ids',
      'recipient_user_ids',jsonb_build_array(owner_id),'exclude_user_ids','[]'::jsonb,
      'title',title,'body',body,'data',payload_data,'event_type',event,'actor_user_id',owner_id,
      'chunk_index',0,'chunk_count',1),60,clock_timestamp(),5)
  on conflict(job_key) do nothing;
  return null;
end;
$$;

revoke all on function public.analysis_cumulative_completion_push() from public,anon,authenticated;

create trigger analysis_enqueue_cumulative_completion_push
after insert on public.analysis_observed_artifacts for each row
when (new.source_profile='cumulative.v1')
execute function public.analysis_cumulative_completion_push();

commit;
