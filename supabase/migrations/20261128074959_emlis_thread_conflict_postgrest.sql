-- PostgREST 14 retries SQLSTATE 40001 inside an RPC. Return the same public
-- conflict code in an HTTP 409 response without a retryable SQLSTATE.
do $migration$
declare
  target regprocedure := 'public.emlis_thread_commit(uuid,uuid,uuid,bigint,jsonb,text,jsonb,jsonb,uuid)'::regprocedure;
  body_digest text;
begin
  select md5(prosrc) into strict body_digest from pg_catalog.pg_proc where oid = target;
  if body_digest = 'f2910dfc6a5fe5b204b2ebc06157bbb6' then
    return;
  end if;
  -- The deployed body must match 20261113120241 before rewriting its errors.
  if body_digest <> '4e33847016eee7652a43d7e442ef9667' then
    raise exception 'Unexpected definition of public.emlis_thread_commit';
  end if;
  execute regexp_replace(
    pg_catalog.pg_get_functiondef(target),
    $pattern$raise sqlstate '40001' using message='([a-z_]+)'$pattern$,
    $replacement$raise sqlstate 'PGRST' using message='{"code":"40001","message":"\1","details":null,"hint":null}', detail='{"status":409,"headers":{}}'$replacement$,
    'g'
  );
end;
$migration$;
