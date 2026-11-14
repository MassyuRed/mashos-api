// Real isolated PostgreSQL checks. The map is produced by the existing CPU
// semantic admission/realizer over synthetic sources; there is no model call.
const { PGlite } = require(process.env.Q2_PGLITE_MODULE);
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '../..');
const seed = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const python = process.argv[3];
const owner = '00000000-0000-0000-0000-000000000001';
const other = '00000000-0000-0000-0000-000000000002';
const added = '00000000-0000-0000-0000-000000900001';
const db = new PGlite();
const value = async (sql, args = []) => (await db.query(sql, args)).rows[0].v;
const snapshot = () => value('select public.analysis_cumulative_source_snapshot($1) as v', [owner]);
const sources = async () => value('select public.analysis_map_correction_sources($1,$2) as v',
  [owner, (await snapshot()).members]);
const read = (key, user = owner) => value('select public.analysis_map_correction_read($1,$2) as v', [user, key]);
const submit = (fx, key, options = {}) => value(
  'select public.analysis_map_correction_submit($1,$2,$3,$4,$5,$6,$7,$8) as v',
  [options.user || owner, options.artifact || fx.projection.projection_of,
    options.kind || 'node', options.ref || 'n1', options.field || 'summary',
    options.text || fx.projection.nodes[0].summary,
    options.explanation || 'その読み取りは違います。本人の説明です。', key]);
const fail = (code, fn) => assert.rejects(fn, error => error.code === code);
async function admin(sql, args = []) {
  await db.exec('reset role');
  try { return await db.query(sql, args); }
  finally { await db.exec('set role service_role'); }
}
function compile(snap, duplicate = false) {
  const code = [
    'import json,sys',
    'from test_analysis_semantic_map import candidate,response',
    'import analysis_semantic_map as semantic',
    'snap=json.load(sys.stdin)',
    'prepared=semantic.prepare_semantic_map("' + owner + '",snap)',
    'packet=candidate()',
    'if sys.argv[1]=="duplicate": packet["nodes"][0]["title"]="同同同"',
    'artifact,coverage=semantic.build_semantic_map(prepared,response(prepared,packet))',
    'private=artifact.private_evidence();private["coverage"]=coverage',
    'private["source_record_refs"]=[m["original"]["id"] for m in snap["members"]]',
    'print(json.dumps(dict(snapshot=snap,private=private,projection=artifact.safe_projection(authenticated_owner_scope="' + owner + '"),text=artifact.safe_text_projection(authenticated_owner_scope="' + owner + '")["text"]),ensure_ascii=False))',
  ].join('\n');
  return JSON.parse(execFileSync(python, ['-c', code, duplicate ? 'duplicate' : 'normal'], {
    cwd: root, env: process.env, input: JSON.stringify(snap), encoding: 'utf8',
    timeout: 60000, maxBuffer: 16 * 1024 * 1024,
  }));
}
async function save(fx, snap, force = false) {
  return value('select public.analysis_cumulative_commit($1,$2,$3,$4,$5,$6,$7,$8,p_force:=$9) as v',
    [owner, snap.guard, fx.projection.projection_of.split('@')[0], fx.private,
      fx.projection, fx.text, snap.period_start, snap.period_end, force]);
}

async function run() {
  await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
    create schema auth; create table auth.users(id uuid primary key);
    create table public.profiles(id uuid primary key references auth.users(id) on delete cascade,subscription_tier text);
    create table public.emotions(id uuid primary key,user_id uuid references auth.users(id) on delete cascade,
      created_at timestamp,memo text,memo_action text,category text[],emotions text[],emotion_details jsonb);
    grant usage on schema public to anon,authenticated,service_role;
    grant all on public.profiles,public.emotions to service_role;`);
  for (const file of [
    '20260911020509_emlis_input_threads_q2.sql',
    '20260911041749_emlis_q3_plan_rounds.sql',
    '20261003134440_analysis_observed_artifacts.sql',
    '20261004041627_analysis_period_comparison.sql',
    '20261101010000_emlis_natural_related_context.sql',
    '20261101080144_cumulative_watashi_map.sql',
    '20261107071033_analysis_semantic_map_wire.sql',
    '20261114032520_analysis_interpretation_correction_sources.sql',
    '20261114123000_analysis_emlis_material_handoff.sql',
    '20261114132000_analysis_map_interpretation_corrections.sql',
  ]) await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations', file), 'utf8'));
  await db.query('insert into auth.users values($1),($2)', [owner, other]);
  await db.query("insert into public.profiles values($1,'premium'),($2,'premium')", [owner, other]);
  for (const { original: r } of seed.members) {
    await db.query('insert into public.emotions values($1,$2,$3,$4,$5,$6,$7,$8)',
      [r.id, owner, r.created_at, r.memo, r.memo_action, r.category, r.emotions, r.emotion_details]);
  }
  await db.exec('set role service_role');
  const snap = await snapshot();
  const fx = compile(snap);
  const artifactId = await save(fx, snap);
  const before = await value('select to_jsonb(a) as v from public.analysis_observed_artifacts a where id=$1', [artifactId]);
  const monthsBefore = await value('select jsonb_agg(to_jsonb(m) order by snapshot_month) as v from public.analysis_cumulative_months m');
  assert.deepEqual(await sources(), []);
  await fail('P0002', () => submit(fx, 'foreign', { user: other }));
  await fail('22023', () => submit(fx, 'bad-version', { artifact: fx.projection.projection_of.replace('@1', '@2') }));
  await fail('22023', () => submit(fx, 'bad-node', { ref: 'n99' }));
  await fail('22023', () => submit(fx, 'bad-field', { field: 'evidence_refs' }));
  await fail('22023', () => submit(fx, 'not-literal', { text: '表示されていない内容' }));
  await fail('22023', () => submit(fx, 'too-long', { explanation: 'あ'.repeat(2001) }));

  const node = await submit(fx, 'node');
  assert.equal(node.source_state, 'ACTIVE');
  assert.equal(node.schema_version, 'cocolon.analysis.map_correction.v1');
  assert.deepEqual(Object.keys(node).sort(), ['correction_id', 'explanation', 'owner_scope', 'recorded_at',
    'schema_version', 'source_state', 'target_context'].sort());
  assert.equal(node.explanation.source_role, 'USER_ANALYSIS_MAP_CORRECTION');
  assert.equal(node.target_context.field_text, fx.projection.nodes[0].summary);
  assert.equal(node.target_context.cohort.length, 1);
  assert.match(node.target_context.cohort[0].source_guard, /^analysis-map-member-v1:[0-9a-f]{64}$/);
  assert.deepEqual(Object.keys(node.target_context.cohort[0]).sort(), ['record_ref', 'source_guard']);
  assert.deepEqual(await submit(fx, 'node'), node);
  assert.deepEqual(await read('node'), node);
  await fail('P0002', () => read('node', other));
  await fail('23505', () => submit(fx, 'node', { explanation: '別の説明です。' }));
  const edge = await submit(fx, 'edge', { kind: 'edge', ref: 'e1', field: 'explanation', text: fx.projection.edges[0].explanation });
  const overview = await submit(fx, 'overview', { kind: 'overview', ref: 'overview', field: 'summary', text: fx.projection.overview.summary });
  assert.equal(edge.target_context.cohort.length, 2);
  assert.equal(overview.target_context.cohort.length, 2);
  const context = await submit(fx, 'context', { field: 'context.0', text: fx.projection.nodes[0].context[0] });
  const unknown = await submit(fx, 'unknown', { ref: 'n2', field: 'unknowns.0', text: fx.projection.nodes[1].unknowns[0] });
  assert.equal(context.source_state, 'ACTIVE');
  assert.equal(unknown.source_state, 'ACTIVE');
  await fail('22023', () => submit(fx, 'bad-array', { field: 'context.99' }));
  await fail('22023', () => submit(fx, 'negative-array', { field: 'context.-1' }));
  await fail('22023', () => submit(fx, 'noncanonical-array', { field: 'context.00' }));
  // The source explanation/control write changes neither the displayed map
  // nor the existing first-of-month capture.
  assert.deepEqual(await value('select to_jsonb(a) as v from public.analysis_observed_artifacts a where id=$1', [artifactId]), before);
  assert.deepEqual(await value('select jsonb_agg(to_jsonb(m) order by snapshot_month) as v from public.analysis_cumulative_months m'), monthsBefore);
  await fail('42501', () => db.query("insert into public.analysis_map_interpretation_corrections(user_id,idempotency_key,request_body,target_context,explanation) values($1,'bypass','{}','{}','x')", [owner]));
  await fail('55000', () => admin("update public.analysis_map_interpretation_corrections set explanation='変更' where id=$1", [node.correction_id]));
  for (const role of ['anon', 'authenticated']) {
    await db.exec('set role ' + role);
    await fail('42501', () => read('node'));
    await fail('42501', () => db.query('select * from public.analysis_map_interpretation_corrections'));
    await db.exec('set role service_role');
  }

  const duplicateSnapshot = await snapshot();
  const duplicate = compile(duplicateSnapshot, true);
  const duplicateId = await save(duplicate, duplicateSnapshot, true);
  await fail('22023', () => submit(duplicate, 'overlapping', { field: 'title', text: '同同' }));
  await fail('22023', () => submit(duplicate, 'cross-object', { ref: 'n2', field: 'title', text: duplicate.projection.nodes[0].title }));
  // A correction outlives its superseded current cache. The first map's
  // monthly reference is retained, while this unreferenced test map is gone.
  const replay = await submit(duplicate, 'cache-replay', { field: 'title', text: duplicate.projection.nodes[0].title });
  await admin('delete from public.analysis_observed_artifacts where id=$1', [duplicateId]);
  assert.deepEqual(await submit(duplicate, 'cache-replay', { field: 'title', text: duplicate.projection.nodes[0].title }), replay);

  await admin("insert into public.emotions values($1,$2,now() at time zone 'UTC' - interval '1 second','新しい記録','',array['生活'],array['平穏'],'[]')", [added, owner]);
  assert((await sources()).every(row => row.source_state === 'ACTIVE'));
  // A fresh correction cannot attach to a source guard that the person no
  // longer sees as the current cohort, even if an old monthly map is readable.
  await fail('40001', () => submit(fx, 'stale-submit'));

  await admin("update public.emotions set memo=memo || '追記。' where id=$1", [seed.members[0].original.id]);
  assert.equal((await read('node')).source_state, 'STALE');
  assert.equal((await read('edge')).source_state, 'STALE');
  assert.equal((await read('overview')).source_state, 'STALE');
  assert.equal((await read('unknown')).source_state, 'ACTIVE');
  assert.deepEqual(await value('select to_jsonb(a) as v from public.analysis_observed_artifacts a where id=$1', [artifactId]), before);
  assert.deepEqual(await value('select jsonb_agg(to_jsonb(m) order by snapshot_month) as v from public.analysis_cumulative_months m'), monthsBefore);
  // A source-bearing thread/answer is not a map-correction container. Adding
  // one as a separate fixture only checks that dependency changes invalidate
  // the old correction; none of the correction RPCs creates such a row.
  const threadId = '00000000-0000-0000-0000-000000900002';
  await admin(`insert into public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
    select $1,$2,e.id,1,'COMPLETED',0,public.emlis_parent_source(e),'{"runtime_profile":"q2.free.one_round.v1"}'::jsonb
    from public.emotions e where e.id=$3`, [threadId, owner, seed.members[1].original.id]);
  await admin(`insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,payload)
    values('00000000-0000-0000-0000-000000900003',$1,1,'ANSWER',1,'separate-source-question',
    '{"source":{"answer_text_private":"別の本人補足。"}}')`, [threadId]);
  assert.equal((await read('unknown')).source_state, 'STALE');
  await admin('delete from public.emotions where id=$1', [seed.members[0].original.id]);
  // Dependency deletion erases the complete derived row, not merely its
  // ACTIVE flag. This includes AI field_text/target_text, explanation and the
  // original request body; no separate explanation-retention rule is added.
  for (const key of ['node', 'edge', 'overview', 'context', 'cache-replay']) {
    await fail('P0002', () => read(key));
  }
  await fail('P0002', () => submit(fx, 'node'));
  const remaining = await sources();
  assert.deepEqual(remaining.map(row => row.correction_id), [unknown.correction_id]);
  assert.equal(await value('select count(*)::int as v from public.analysis_map_interpretation_corrections where id=any($1::uuid[])',
    [[node.correction_id, edge.correction_id, overview.correction_id, context.correction_id, replay.correction_id]]), 0);
  assert.equal(await value('select count(*)::int as v from public.analysis_map_interpretation_corrections where user_id=$1', [owner]), 1);
  assert.equal((await read('unknown')).source_state, 'STALE');
  // Moving the remaining source to another owner has the same old-owner
  // privacy boundary as deletion. Roll back only to reuse this fixture for
  // the independent account-cascade check below.
  await db.exec('begin');
  try {
    await admin('update public.emotions set user_id=$1 where id=$2', [other, seed.members[1].original.id]);
    await db.exec('savepoint missing_old_owner');
    await fail('P0002', () => read('unknown'));
    await db.exec('rollback to savepoint missing_old_owner');
    await db.exec('savepoint missing_new_owner');
    await fail('P0002', () => read('unknown', other));
    await db.exec('rollback to savepoint missing_new_owner');
    assert.deepEqual(await sources(), []);
    assert.deepEqual(await value('select public.analysis_map_correction_sources($1,public.analysis_cumulative_source_snapshot($1)->\'members\') as v', [other]), []);
    assert.equal(await value('select count(*)::int as v from public.analysis_map_interpretation_corrections'), 0);
  } finally { await db.exec('rollback'); }
  assert.equal((await read('unknown')).source_state, 'STALE');
  await admin('delete from auth.users where id=$1', [owner]);
  assert.equal(await value('select count(*)::int as v from public.analysis_map_interpretation_corrections'), 0);
  console.log(JSON.stringify({status:'passed',scope:'map correction SQL/owner/target/cohort/idempotency/immutability/dependency erasure',
    operations:6,model_calls:0,live_database:false}));
  await db.close();
}
run().catch(error => {
  console.error({message:error.message,code:error.code,position:error.position,where:error.where,stack:error.stack});
  process.exitCode = 1;
});
