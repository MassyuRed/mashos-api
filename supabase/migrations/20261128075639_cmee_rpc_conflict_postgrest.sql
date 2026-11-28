-- The hosted PostgREST 14 pool can retry SQLSTATE 40001 forever. These
-- RPCs deliberately reject stale requests. Return the same public conflict
-- code and reason through PostgREST without a retryable database SQLSTATE.
do $migration$
declare
  target record;
  target_id regprocedure;
  body_digest text;
  definition text;
begin
  for target in
    select * from (values
      ('public.analysis_cumulative_commit(uuid,text,text,jsonb,jsonb,text,timestamp with time zone,timestamp with time zone,uuid,boolean)',
       '7de18964a0e74f3c45d4f33b2aaeee2c', '7d0e2e5ba7f9b84ff93f444e6caff086'),
      ('public.analysis_if_artifact_delete(uuid,text,uuid)',
       'e664e92957a23c0bcfc7bee4871935e7', 'fbe2293c17856ac24f9da3165fb13c0a'),
      ('public.analysis_if_artifacts_read(uuid,text,uuid,integer,integer,text,text,text)',
       '97b1cdfb2d08964d5e9468e50cbe1e75', '00583ab8930019d969b6b2c5377a2a0e'),
      ('public.analysis_if_intent_commit(uuid,text,text,text,jsonb)',
       'bed01a4e5248ce34a0e75fecef316bb3', '2c7b2214dc38d6e54491a4364fb072b1'),
      ('public.analysis_if_operation_fail(uuid,text,uuid)',
       'e7f893818b03110264e3df12b404f496', 'a454d20a2f0ed069119c35f27e74999a'),
      ('public.analysis_if_operation_receive(uuid,text,uuid,jsonb)',
       '1d839c5a7abf3cf36c8c82ad9c193832', '2ba83e4ded3c4cff834e971ca5428a14'),
      ('public.analysis_if_operation_reserve(uuid,text,text,text,text,jsonb,boolean)',
       'd071b26aa439079eede9dbcecce23b2f', '9460d094a51b3fde38aa89fece02d0ac'),
      ('public.analysis_if_operation_start(uuid,text,uuid)',
       '17d98718f75793e3622f786999934016', '5aae634f0e641481af26b9fd24e2111c'),
      ('public.analysis_if_set_commit(uuid,text,text,text,text,jsonb)',
       'a9dce56e8c7930c359a9404f0f3f4b22', 'a815d0d4fe8c211ce1542deb3624d61f'),
      ('public.analysis_map_correction_submit_original_field(uuid,text,text,text,text,text,text,text)',
       '5a3458d4e629ea9b2b4eb6116ffebcb2', 'ca0390c0c31397e0b840cc842ea92b43'),
      ('public.analysis_map_correction_submit(uuid,text,text,text,text,text,text,text,text)',
       '46a950b5379ad287cbdbb396c7a862e9', '244ec0dd540c0a49bf8ccb29a64aff30'),
      ('public.analysis_observed_commit(uuid,timestamp with time zone,timestamp with time zone,text,text,text,text,jsonb,jsonb,text)',
       '0ebb84da98ccdf0eea129ba073bc621e', '26c1d87b541415b409d1f4c00922f772'),
      ('public.deep_insight_issue_grounded(uuid,date,text,text,text,text,text,text,jsonb)',
       '18342324325ce0e4adf8675728befc1d', '2d469f10341d9877d97a54d18881ad98')
    ) as functions(signature, before_md5, after_md5)
  loop
    target_id := target.signature::regprocedure;
    select md5(prosrc) into strict body_digest from pg_catalog.pg_proc where oid = target_id;
    if body_digest = target.after_md5 then
      continue;
    end if;
    if body_digest <> target.before_md5 then
      raise exception 'Unexpected definition of %', target.signature;
    end if;

    definition := regexp_replace(
      pg_catalog.pg_get_functiondef(target_id),
      $pattern$raise sqlstate '40001' using message='([a-z_]+)'$pattern$,
      $replacement$raise sqlstate 'PGRST' using message='{"code":"40001","message":"\1","details":null,"hint":null}', detail='{"status":409,"headers":{}}'$replacement$,
      'g'
    );
    definition := replace(
      definition,
      $pattern$raise sqlstate '40001';$pattern$,
      $replacement$raise sqlstate 'PGRST' using message='{"code":"40001","message":"40001","details":null,"hint":null}', detail='{"status":409,"headers":{}}';$replacement$
    );
    execute definition;

    select md5(prosrc) into strict body_digest from pg_catalog.pg_proc where oid = target_id;
    if body_digest <> target.after_md5 then
      raise exception 'Unexpected rewritten definition of %', target.signature;
    end if;
  end loop;
end;
$migration$;
