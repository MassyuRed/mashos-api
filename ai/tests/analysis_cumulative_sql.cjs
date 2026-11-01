// Real PostgreSQL semantics in PGlite, using real compiler output from Python.
const { PGlite } = require('@electric-sql/pglite');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const fx = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const root = path.resolve(__dirname, '../..');
const db = new PGlite();
const owner='00000000-0000-0000-0000-000000000001', other='00000000-0000-0000-0000-000000000002';
async function value(sql,params=[]) { return (await db.query(sql,params)).rows[0].v; }
async function snap() { return value('select public.analysis_cumulative_source_snapshot($1) as v',[owner]); }
async function read(history=false, id=null, month=null, offset=0) {
  return value('select public.analysis_cumulative_read($1,$2,$3,200,$4,$5) as v',[owner,id,history,offset,month]);
}
async function commit(s, extra={}) {
  const candidate=extra.fixture || fx;
  return value('select public.analysis_cumulative_commit($1,$2,$3,$4,$5,$6,$7,$8) as v',[
    owner,s.guard,extra.id || candidate.projection.projection_of.split('@')[0],candidate.private,candidate.projection,candidate.text,s.period_start,s.period_end]);
}
(async()=>{
  await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
    create schema auth; create table auth.users(id uuid primary key);
    create table public.profiles(id uuid primary key references auth.users(id) on delete cascade,subscription_tier text);
    create table public.emotions(id uuid primary key,user_id uuid references auth.users(id) on delete cascade,
      created_at timestamp,memo text,memo_action text,category text[],emotions text[],emotion_details jsonb);
    grant usage on schema public to anon,authenticated,service_role;
    grant all on public.profiles,public.emotions to service_role;`);
  for(const file of ['20260911020509_emlis_input_threads_q2.sql','20260911041749_emlis_q3_plan_rounds.sql',
    '20261003134440_analysis_observed_artifacts.sql','20261004041627_analysis_period_comparison.sql',
    '20261101080144_cumulative_watashi_map.sql']) {
    await db.exec(fs.readFileSync(path.join(root,'supabase/migrations',file),'utf8'));
  }
  await db.query('insert into auth.users values($1),($2)',[owner,other]);
  await db.query("insert into public.profiles values($1,'free'),($2,'plus')",[owner,other]);
  for(const {original:r} of fx.snapshot.members) {
    await db.query('insert into public.emotions values($1,$2,$3,$4,$5,$6,$7,$8)',
      [r.id,owner,r.created_at,r.memo,r.memo_action,r.category,r.emotions,r.emotion_details]);
  }
  let s=await snap(); assert.equal(s.members.length,201);
  await db.exec('set role service_role');
  assert.equal(await commit(s),fx.id);
  let current=await read(); assert.equal(current.items.length,1);
  assert.equal(current.items[0].content_text,fx.text);
  assert.deepEqual(current.items[0].content_json.watashiMap,fx.projection);
  assert.equal((await read(true)).items.length,1);
  assert.equal((await value('select public.analysis_cumulative_read($1) as v',[other])).items.length,0);
  const month=(await read(true)).items[0].snapshot_month;
  const captured=(await read(true)).items[0].captured_at;
  await value('select public.analysis_cumulative_commit($1,$2,p_existing_id:=$3) as v',[owner,s.guard,fx.id]);
  assert.equal((await read(true)).items[0].captured_at,captured);
  // Stored months survive an upgrade/downgrade, and rank is applied before ID/offset.
  await db.exec('reset role');
  await db.query(`insert into public.analysis_cumulative_months(user_id,snapshot_month,artifact_id,captured_at)
    select $1,($2::date - make_interval(months=>g))::date,$3,clock_timestamp()
    from generate_series(1,14) g`,[owner,month,fx.id]);
  assert.equal((await read(true)).items.length,2);
  const oldest=await value('select min(snapshot_month)::text as v from public.analysis_cumulative_months');
  assert.equal((await read(false,fx.id,oldest)).items.length,0);
  assert.equal((await read(true,null,null,2)).items.length,0);
  const guardBefore=(await snap()).guard;
  await db.query("update public.profiles set subscription_tier='plus' where id=$1",[owner]);
  assert.equal((await snap()).guard,guardBefore);
  assert.equal((await read(true)).items.length,12);
  await db.query("update public.profiles set subscription_tier='premium' where id=$1",[owner]);
  assert.equal((await read(true)).items.length,15);
  await db.query("update public.profiles set subscription_tier='free' where id=$1",[owner]);
  assert.equal(await value('select count(*)::int as v from public.analysis_cumulative_months'),15);
  // Original edit dirties current but leaves the captured text and graph immutable.
  await db.query("update public.emotions set memo='私は仕事を続けなかった。' where id=$1",[fx.snapshot.members[0].original.id]);
  assert.equal((await read()).items.length,0);
  assert.equal((await read(true)).items[0].content_text,fx.text);
  await assert.rejects(()=>commit(s),e=>e.code==='40001');
  const node=fx.projection.nodes[0].node_ref;
  const evidence=await value('select public.analysis_cumulative_evidence($1,$2,$3) as v',[owner,fx.id,node]);
  assert.equal(evidence.items.length,201);
  assert(!JSON.stringify(await read(true)).includes('private_evidence'));
  for(const role of ['anon','authenticated']) {
    await db.exec('set role '+role);
    await assert.rejects(()=>read(true),e=>e.code==='42501');
    await assert.rejects(()=>db.query('select * from public.analysis_cumulative_months'),e=>e.code==='42501');
    await db.exec('reset role');
  }
  // Actual source deletion removes derivative maps and their month references.
  await db.query('delete from public.emotions where id=$1',[fx.snapshot.members[100].original.id]);
  assert.equal(await value('select count(*)::int as v from public.analysis_observed_artifacts'),0);
  assert.equal(await value('select count(*)::int as v from public.analysis_cumulative_months'),0);
  // Even a source excluded from ordinary analysis remains a deletion dependency.
  await db.query('delete from public.emotions where user_id=$1',[owner]);
  for(const {original:r} of fx.safety_case.snapshot.members) {
    await db.query('insert into public.emotions values($1,$2,$3,$4,$5,$6,$7,$8)',
      [r.id,owner,r.created_at,r.memo,r.memo_action,r.category,r.emotions,r.emotion_details]);
  }
  await commit(await snap(),{fixture:fx.safety_case});
  assert.equal((await read(true)).items[0].content_json.map_context.excluded_count,1);
  await db.query('delete from public.emotions where id=$1',[fx.safety_case.snapshot.members[1].original.id]);
  assert.equal(await value('select count(*)::int as v from public.analysis_observed_artifacts'),0);
  assert.equal(await value('select count(*)::int as v from public.analysis_cumulative_months'),0);
  await db.query('delete from auth.users where id=$1',[owner]);
  console.log(JSON.stringify({status:'passed',sourceRecords:201,monthlyReferences:15,scope:'cumulative SQL/owner/rank/immutability/deletion'}));
  await db.close();
})().catch(e=>{console.error({message:e.message,code:e.code,position:e.position,where:e.where});process.exitCode=1;});
