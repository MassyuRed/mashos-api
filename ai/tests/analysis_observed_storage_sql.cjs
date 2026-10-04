// Synthetic PostgreSQL behavior checks. Run with PGlite installed outside the repo:
// NODE_PATH=/tmp/cocolon-analysis-db-check/node_modules node ai/tests/analysis_observed_storage_sql.cjs <fixture.json>
// Fixture is produced by await test_analysis_observed_storage.storage_sql_fixture(), not user data.
const { PGlite } = require('@electric-sql/pglite');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { performance } = require('node:perf_hooks');
const root = path.resolve(__dirname, '../..');
const fx = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const owner = '00000000-0000-0000-0000-000000000001';
const other = '00000000-0000-0000-0000-000000000002';
const start = '2026-10-01T00:00:00+00:00', end = '2026-10-03T00:00:00+00:00';
const db = new PGlite();
let checks = 0;
async function expectError(action, code) {
  await assert.rejects(action, e => e.code === code);
  checks++;
}
async function one(sql, params=[]) { return (await db.query(sql, params)).rows[0]; }
async function count() { return Number((await one('select count(*) as n from public.analysis_observed_artifacts')).n); }
async function snapshot(mode='standard', type='latest') {
  return (await one('select public.analysis_observed_source_snapshot($1,$2,$3,$4,$5) as value',
    [owner,start,end,mode,type])).value;
}
async function commit(guard, mode='standard', type='latest', projection=fx.row.content_json.watashiMap) {
  return (await one('select public.analysis_observed_commit($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) as id',
    [owner,start,end,mode,type,guard,projection.projection_of?.split('@')[0] || fx.row.content_json.watashiMap.projection_of.split('@')[0],
     fx.private,projection,fx.row.content_text])).id;
}
async function read(who=owner, history=false) {
  return (await one('select public.analysis_observed_read($1,p_history:=$2) as value',[who,history])).value;
}
async function insertEmotion(id, created='2026-10-01T01:00:00') {
  await db.query(`insert into public.emotions(id,user_id,created_at,memo,memo_action,category,emotions,emotion_details)
    values($1,$2,$3,$4,$5,$6,$7,$8)`,[id,owner,created,fx.original.memo,fx.original.memo_action,
      fx.original.category,fx.original.emotions,fx.original.emotion_details]);
}
(async()=>{
  await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
    create schema auth; create table auth.users(id uuid primary key);
    create table public.profiles(id uuid primary key references auth.users(id) on delete cascade,subscription_tier text);
    create table public.emotions(id uuid primary key,user_id uuid references auth.users(id) on delete cascade,
      created_at timestamp,memo text,memo_action text,category text[],emotions text[],emotion_details jsonb);
    grant usage on schema public to anon,authenticated,service_role;
    grant all on public.profiles,public.emotions to service_role;
    grant insert,update,delete on public.emotions to authenticated;
    alter default privileges grant all on tables to anon,authenticated,service_role;`);
  for (const file of ['20260911020509_emlis_input_threads_q2.sql','20260911041749_emlis_q3_plan_rounds.sql',
      '20261003134440_analysis_observed_artifacts.sql']) {
    await db.exec(fs.readFileSync(path.join(root,'supabase/migrations',file),'utf8'));
  }
  checks++;
  await db.query('insert into auth.users values($1),($2)',[owner,other]);
  await db.query("insert into public.profiles values($1,'plus'),($2,'plus')",[owner,other]);
  await insertEmotion(fx.original.id);
  const snap = await snapshot();
  assert.equal(snap.members.length,1); assert.match(snap.guard,/^analysis-db-v1:[0-9a-f]{64}$/); checks++;
  await db.exec('set role service_role');
  const t0 = performance.now();
  assert.equal(await commit(snap.guard),fx.row.id);
  const committedMs=performance.now()-t0;
  assert.equal(await commit(snap.guard),fx.row.id); assert.equal(await count(),1); checks++;
  const t1=performance.now(), visible=await read(), readMs=performance.now()-t1;
  assert.deepEqual(visible.items[0].content_json,fx.row.content_json);
  assert.equal(visible.items[0].content_text,fx.row.content_text);
  assert(!JSON.stringify(visible).includes('private_evidence')); assert(!JSON.stringify(visible).includes(snap.guard)); checks++;
  // Upgrade with an existing immutable row, then read identical saved bytes.
  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root,'supabase/migrations/20261004041627_analysis_period_comparison.sql'),'utf8'));
  await db.exec('set role service_role');
  assert.deepEqual(await read(),visible); checks++;
  assert.equal((await read(other)).items.length,0); checks++;
  assert.equal((await one('select public.analysis_observed_read($1,p_days:=28) as value',[owner])).value.items.length,0);
  assert.equal((await one('select public.analysis_observed_read($1,p_days:=2) as value',[owner])).value.items.length,1); checks++;
  await db.exec('reset role');
  await db.exec('begin isolation level repeatable read');
  await expectError(()=>commit(snap.guard),'40001');
  await db.exec('rollback');
  await expectError(()=>db.exec("update public.analysis_observed_artifacts set content_text='changed'"),'55000');
  for(const role of ['anon','authenticated']) {
    await db.exec('set role '+role);
    await expectError(()=>db.exec('select * from public.analysis_observed_artifacts'),'42501');
    await expectError(()=>snapshot(),'42501');
    await expectError(()=>read(),'42501');
    await db.exec('reset role');
  }
  await db.exec("update public.profiles set subscription_tier='plus'");
  assert.equal(await count(),1); checks++;
  await db.exec('set role authenticated');
  await db.query("update public.emotions set memo='私は考えをノートに書かなかった。'");
  await db.exec('reset role');
  assert.equal(await count(),0); checks++;
  await expectError(()=>commit(snap.guard),'40001');
  await expectError(()=>commit((undefined), 'standard'),'40001');
  const edited=await snapshot();
  await expectError(()=>commit(edited.guard,'standard','latest',{}),'23514');
  await commit(edited.guard);
  // Even if invalidation is missed, read-time source reconciliation denies it.
  await db.exec('alter table public.emotions disable trigger analysis_emotions_changed');
  await db.exec("update public.emotions set memo='別の合成入力'");
  assert.equal((await read()).items.length,0); checks++;
  await db.exec('alter table public.emotions enable trigger analysis_emotions_changed');
  // New data after the frozen interval still dirties latest.
  await insertEmotion('00000000-0000-0000-0000-000000000102','2026-10-03T01:00:00');
  assert.equal(await count(),0); checks++;
  await commit((await snapshot()).guard);
  const tid='00000000-0000-0000-0000-000000000201';
  await db.query(`insert into public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
    select $1,$2,id,1,'COMPLETED',0,public.emlis_parent_source(e),'{}' from public.emotions e where id=$3`,
    [tid,owner,fx.original.id]);
  assert.equal(await count(),0); checks++;
  await commit((await snapshot()).guard);
  await db.query(`insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,payload)
    values('00000000-0000-0000-0000-000000000301',$1,1,'ANSWER',1,'q','{"source":{"answer_text_private":"synthetic answer"}}')`,[tid]);
  assert.equal(await count(),0); checks++;
  await commit((await snapshot()).guard);
  await db.query('delete from public.emlis_input_threads where id=$1',[tid]);
  assert.equal(await count(),0); checks++;
  await commit((await snapshot()).guard);
  await db.query("update public.profiles set subscription_tier='free' where id=$1",[owner]);
  assert.equal(await count(),0); checks++;
  await expectError(()=>snapshot('deep'),'42501');
  await expectError(()=>snapshot('light','monthly'),'42501');
  await expectError(()=>read(owner,true),'42501');
  const free=await snapshot('light');
  await commit(free.guard,'light');
  assert.equal((await read()).items.length,1); checks++;
  await db.query('delete from public.emotions where id=$1',[fx.original.id]);
  assert.equal(await count(),0); checks++;
  await insertEmotion(fx.original.id);
  await commit((await snapshot('light')).guard,'light');
  await db.query('delete from auth.users where id=$1',[owner]);
  assert.equal(await count(),0); checks++;
  // Real two-period save/read lifecycle, including changes only in the baseline.
  const compared=fx.comparison, firstUse=fx.empty_comparison;
  async function comparisonSnapshot() {
    return (await one('select public.analysis_observed_comparison_snapshot($1,$2,$3,$4,$5) as value',
      [owner,start,end,'standard','monthly'])).value;
  }
  async function comparisonCommit(snap, candidate=compared) {
    return (await one('select public.analysis_observed_commit($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) as id',
      [owner,start,end,'standard','monthly',snap.guard,candidate.row.content_json.watashiMap.projection_of.split('@')[0],
       candidate.private,candidate.row.content_json.watashiMap,candidate.row.content_text])).id;
  }
  async function comparisonRead() {
    return (await one("select public.analysis_observed_read($1,p_report_type:='monthly',p_history:=true) as value",[owner])).value;
  }
  async function insertPrevious(id=compared.previous_original.id) {
    const p=compared.previous_original;
    await db.query(`insert into public.emotions(id,user_id,created_at,memo,memo_action,category,emotions,emotion_details)
      values($1,$2,$3,$4,$5,$6,$7,$8)`,[id,owner,p.created_at,p.memo,p.memo_action,p.category,p.emotions,p.emotion_details]);
  }
  await db.query('insert into auth.users values($1)',[owner]);
  await db.query("insert into public.profiles values($1,'plus')",[owner]);
  await insertEmotion(fx.original.id);
  const empty=await comparisonSnapshot();
  assert(empty.comparison_eligible); assert.equal(empty.previous.members.length,0);
  await comparisonCommit(empty,firstUse);
  assert.equal((await comparisonRead()).items[0].content_json.watashiMap.period_comparison.state,'NO_PREVIOUS'); checks++;
  await insertPrevious(); assert.equal(await count(),0); checks++;
  await expectError(()=>comparisonCommit(empty,firstUse),'40001');
  const originalZone=(await one('show timezone')).TimeZone;
  await db.exec("set timezone='America/New_York'");
  const dst=(await one("select public.analysis_observed_comparison_snapshot($1,'2026-03-09T00:00:00Z','2026-03-10T00:00:00Z','standard','latest') as v",[owner])).v;
  assert.equal(Date.parse(dst.previous_end)-Date.parse(dst.previous_start),86400000); checks++;
  await db.query("select set_config('TimeZone',$1,false)",[originalZone]);
  const pair=await comparisonSnapshot();
  assert.equal(pair.previous.members.length,1); assert.equal(pair.current.members.length,1);
  assert.match(pair.guard,/^analysis-db-compare-v1:[0-9a-f]{64}$/); checks++;
  await db.exec('set role service_role');
  await commit((await snapshot('standard','monthly')).guard,'standard','monthly');
  await comparisonCommit(pair); await comparisonCommit(pair);
  assert.equal(await count(),2); checks++;
  const visiblePair=(await comparisonRead()).items.find(x=>x.id===compared.row.id);
  assert.deepEqual(visiblePair.content_json,compared.row.content_json);
  assert.equal(visiblePair.content_text,compared.row.content_text);
  assert(!JSON.stringify(visiblePair).includes('previous_evidence'));
  assert(!JSON.stringify(visiblePair).includes(pair.guard)); checks++;
  assert.equal((await read(other,true)).items.length,0); checks++;
  await db.exec('reset role');
  for (const role of ['anon','authenticated']) {
    await db.exec('set role '+role);
    await expectError(()=>comparisonSnapshot(),'42501');
    await expectError(()=>comparisonCommit(pair),'42501');
    await db.exec('reset role');
  }
  const singleGuard=(await snapshot('standard','monthly')).guard;
  await expectError(()=>comparisonCommit({...pair,guard:singleGuard}),'23514');
  const broken=JSON.parse(JSON.stringify(compared));
  broken.private.period_comparison.previous_artifact_ref=broken.private.projection_of;
  await expectError(()=>comparisonCommit(pair,broken),'23514');
  // Previous-only edit removes the comparison but keeps the single-period row.
  await db.query("update public.emotions set memo='私は考えをノートに書いた。' where id=$1",[compared.previous_original.id]);
  assert.equal(await count(),1); assert.equal((await comparisonRead()).items.length,1); checks++;
  await expectError(()=>comparisonCommit(pair),'40001');
  await comparisonCommit(await comparisonSnapshot());
  await db.exec('alter table public.emotions disable trigger analysis_emotions_changed');
  await db.query("update public.emotions set memo='私は考えをノートに書かなかった。' where id=$1",[compared.previous_original.id]);
  assert.equal(await count(),2); assert.equal((await comparisonRead()).items.length,1); checks++;
  await db.exec('alter table public.emotions enable trigger analysis_emotions_changed');
  await db.query('delete from public.analysis_observed_artifacts where id=$1',[compared.row.id]);
  await comparisonCommit(await comparisonSnapshot());
  const previousThread='00000000-0000-0000-0000-000000000299';
  await db.query(`insert into public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
    select $1,$2,id,1,'COMPLETED',0,public.emlis_parent_source(e),'{}' from public.emotions e where id=$3`,
    [previousThread,owner,compared.previous_original.id]);
  assert.equal(await count(),1); checks++;
  await comparisonCommit(await comparisonSnapshot());
  await db.query(`insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,payload)
    values('00000000-0000-0000-0000-000000000399',$1,1,'ANSWER',1,'q','{"source":{"answer_text_private":"synthetic correction"}}')`,[previousThread]);
  assert.equal(await count(),1); checks++;
  await comparisonCommit(await comparisonSnapshot());
  await db.query('delete from public.emlis_thread_events where thread_id=$1',[previousThread]);
  assert.equal(await count(),1); checks++;
  await comparisonCommit(await comparisonSnapshot());
  await db.query('delete from public.emlis_input_threads where id=$1',[previousThread]);
  assert.equal(await count(),1); checks++;
  await comparisonCommit(await comparisonSnapshot());
  await db.query('delete from public.emotions where id=$1',[compared.previous_original.id]);
  assert.equal(await count(),1); checks++;
  await comparisonCommit(await comparisonSnapshot(),firstUse);
  await db.query('delete from public.emotions where id=$1',[fx.original.id]);
  assert.equal(await count(),0); checks++;
  await insertEmotion(fx.original.id); await insertPrevious();
  await db.query('update public.emotions set memo=$1 where id=$2',[fx.original.memo,compared.previous_original.id]);
  await comparisonCommit(await comparisonSnapshot(),fx.unchanged_comparison);
  const unchanged=(await comparisonRead()).items[0];
  assert.deepEqual(unchanged.content_json.watashiMap.period_comparison,
    {state:'COMPARABLE',reason_codes:[],safe_change_kinds:[]});
  assert.equal(unchanged.content_text,fx.unchanged_comparison.row.content_text); checks++;
  await db.query('delete from public.analysis_observed_artifacts');
  // Force only the baseline out of retention without changing the tier:
  // same effect as time advancing across a retention boundary.
  await db.query('update public.emotions set memo=$1 where id=$2',[compared.previous_original.memo,compared.previous_original.id]);
  await comparisonCommit(await comparisonSnapshot());
  await db.exec(`create or replace function public.emlis_parent_visible(p_created timestamp,p_tier text,p_now timestamptz)
    returns boolean language sql stable as $$ select p_created >= timestamp '2026-10-01' $$;`);
  const expired=await comparisonSnapshot();
  assert.equal(expired.comparison_eligible,false); assert.match(expired.guard,/^analysis-db-v1:/);
  assert.equal((await comparisonRead()).items.length,0); checks++;
  await commit(expired.guard,'standard','monthly');
  assert.equal((await comparisonRead()).items[0].content_json.watashiMap.period_comparison.state,'NO_PREVIOUS'); checks++;
  console.log(JSON.stringify({checks,fixture_bytes:Buffer.byteLength(JSON.stringify(fx)),
    commit_ms:Math.round(committedMs),read_ms:Math.round(readMs),environment:'isolated synthetic PGlite; not live latency'}));
  await db.close();
})().catch(async error=>{console.error(error.message,error.code || '',{checks});await db.close();process.exitCode=1;});
