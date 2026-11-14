// Isolated PostgreSQL lifecycle checks with real CPU-compiled IF/Saved artifacts.
// No external DB, generation service, GPU, deployment or network is involved.
const { PGlite } = require(process.env.Q2_PGLITE_MODULE || '@electric-sql/pglite');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');

const initial = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const python = process.env.PYTHON_EXECUTABLE || process.argv[3];
if (!python) throw new Error('Pass the existing test Python via PYTHON_EXECUTABLE or argv[3].');
const root = path.resolve(__dirname, '../..');
const db = new PGlite();
const owner = '00000000-0000-0000-0000-000000000001';
const other = '00000000-0000-0000-0000-000000000002';
const addedId = '00000000-0000-0000-0000-000000900001';
const hash = text => createHash('sha256').update(text).digest('hex');
const setKey = hash('person-if-operation');
const setRequest = hash('same-if-request');
const savedKey = hash('person-saved-operation');
const savedRequest = hash('same-saved-request');
const differentRequest = hash('different-person-request');
const uuidOf = ref => {
  assert.match(ref, /^artifact:[0-9a-f]{32}@1$/);
  const h = ref.slice(9, 41);
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
};

async function value(sql, params = []) {
  return (await db.query(sql, params)).rows[0].v;
}
async function snapshot() {
  return value('select public.analysis_cumulative_source_snapshot($1) as v', [owner]);
}
async function read(kind, id = null, { limit = 60, offset = 0, key = null, request = null, user = owner } = {}) {
  return value('select public.analysis_if_artifacts_read($1,$2,$3,$4,$5,$6,$7) as v',
    [user, kind, id, limit, offset, key, request]);
}
async function context(baseRef, user = owner) {
  return value('select public.analysis_if_base_context($1,$2) as v', [user, baseRef]);
}
async function reserve({ key = setKey, request = setRequest, user = owner, baseRef = null, guard = null, material = null } = {}) {
  return value('select public.analysis_if_operation_reserve($1,$2,$3,$4,$5,$6) as v',
    [user, key, request, baseRef, guard, material]);
}
async function start(token, key = setKey, user = owner) {
  return value('select public.analysis_if_operation_start($1,$2,$3) as v', [user, key, token]);
}
async function receive(token, receipt, key = setKey, user = owner) {
  return value('select public.analysis_if_operation_receive($1,$2,$3,$4) as v', [user, key, token, receipt]);
}
async function fail(token, key = setKey, user = owner) {
  return value('select public.analysis_if_operation_fail($1,$2,$3) as v', [user, key, token]);
}
async function setCommit(storage, baseRef, guard, { key = setKey, request = setRequest, user = owner } = {}) {
  return value('select public.analysis_if_set_commit($1,$2,$3,$4,$5,$6) as v',
    [user, baseRef, guard, key, request, storage]);
}
async function intentCommit(storage, setRef, { key = savedKey, request = savedRequest, user = owner } = {}) {
  return value('select public.analysis_if_intent_commit($1,$2,$3,$4,$5) as v',
    [user, setRef, key, request, storage]);
}
async function remove(kind, id, user = owner) {
  return value('select public.analysis_if_artifact_delete($1,$2,$3) as v', [user, kind, id]);
}
async function admin(sql, params = []) {
  await db.exec('reset role');
  try { return await db.query(sql, params); }
  finally { await db.exec('set role service_role'); }
}
async function tier(value) {
  await admin('update public.profiles set subscription_tier=$1 where id=$2', [value, owner]);
}
const denied = operation => assert.rejects(operation, error => error.code === '42501');
const conflict = operation => assert.rejects(operation, error => error.code === '23505');
const changed = operation => assert.rejects(operation, error => error.code === '40001');
const unavailable = operation => assert.rejects(operation, error => error.code === 'P0002');

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
    '20261101080144_cumulative_watashi_map.sql',
    '20261107071033_analysis_semantic_map_wire.sql',
    '20261114032520_analysis_interpretation_correction_sources.sql',
    '20261114120000_analysis_if_route_artifacts.sql',
  ]) {
    await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations', file), 'utf8'));
  }
  await db.query('insert into auth.users values($1),($2)', [owner, other]);
  // Both are Premium so owner isolation cannot pass merely because of a tier denial.
  await db.query("insert into public.profiles values($1,'premium'),($2,'premium')", [owner, other]);
  for (const { original: row } of initial.base.snapshot.members) {
    await db.query('insert into public.emotions values($1,$2,$3,$4,$5,$6,$7,$8)',
      [row.id, owner, row.created_at, row.memo, row.memo_action, row.category, row.emotions, row.emotion_details]);
  }
  await db.exec('set role service_role');
  const snap = await snapshot();
  assert.equal(snap.members.length, initial.base.snapshot.members.length);
  const baseId = await value('select public.analysis_cumulative_commit($1,$2,$3,$4,$5,$6,$7,$8) as v', [
    owner, snap.guard, initial.base.projection.projection_of.split('@')[0], initial.base.private,
    initial.base.projection, initial.base.text, snap.period_start, snap.period_end,
  ]);
  assert.equal(baseId, initial.base.id);

  // PG jsonb serialization owns the DB-native guard. Compile exactly once with
  // that real guard instead of rewriting hashes/integrity in the fixture JSON.
  const code = [
    'import json, sys',
    'from ai.tests.test_analysis_if_service import sql_fixture',
    'print(json.dumps(sql_fixture(guard=sys.argv[1], base=json.load(sys.stdin)), ensure_ascii=False))',
  ].join('\n');
  const pythonPath = [root, path.join(root, 'ai'), path.join(root, 'ai/services'),
    path.join(root, 'ai/services/ai_inference'), path.join(root, 'ai/tests'), process.env.PYTHONPATH]
    .filter(Boolean).join(path.delimiter);
  const fx = JSON.parse(execFileSync(python, ['-c', code, snap.guard], {
    cwd: root, env: { ...process.env, PYTHONPATH: pythonPath }, timeout: 60000,
    input: JSON.stringify(initial.base), maxBuffer: 32 * 1024 * 1024, encoding: 'utf8',
  }));
  assert.deepEqual(fx.base.projection, initial.base.projection);
  assert.deepEqual(fx.base.private, initial.base.private);
  const baseRef = fx.base.projection.projection_of;
  assert.equal(fx.set_storage.owner_scope, owner);
  assert.equal(fx.saved_storage.owner_scope, owner);
  assert.equal(fx.set_storage.bundle.lifecycle_bindings.version_set.base_source_guard, snap.guard);
  assert.equal(fx.saved_storage.bundle.lifecycle_bindings.version_set.base_source_guard, snap.guard);
  const setId = uuidOf(fx.set_storage.safe_projection.projection_of);
  const savedId = uuidOf(fx.saved_storage.safe_projection.projection_of);
  const setRef = fx.set_storage.bundle.primary_artifact.candidate_set_id + '@1';
  const chosen = fx.saved_storage.bundle.primary_artifact.selected_scenario_ref;
  const base = await context(baseRef);
  assert.equal(base.base_observed_map_ref, baseRef);
  assert.equal(base.base_source_guard, snap.guard);
  assert.equal(base.subscription_tier, 'premium');
  assert.deepEqual(base.base_projection, fx.base.projection);
  assert.deepEqual(base.base_private_evidence, fx.base.private);
  assert.deepEqual(new Set(base.source_record_refs), new Set(snap.members.map(row => row.original.id)));

  await unavailable(() => setCommit(fx.set_storage, baseRef, snap.guard));
  assert.equal(await reserve(), null);
  const operation = await reserve({ baseRef, guard: snap.guard, material: fx.operation_material });
  assert.equal(operation.state, 'RESERVED');
  assert.match(operation.call_token, /^[0-9a-f-]{36}$/);
  assert.equal(operation.material, null);
  const sameReservation = await reserve({ baseRef, guard: snap.guard, material: fx.operation_material });
  assert.equal(sameReservation.operation_id, operation.operation_id);
  assert.equal(sameReservation.call_token, null);
  assert.equal(sameReservation.material, null);
  assert.equal((await read('scenario_set')).items.length, 0);
  await conflict(() => reserve({ request: differentRequest }));
  assert.deepEqual(await start(other), { started: false });
  assert.deepEqual(await receive(operation.call_token, fx.provider_receipt), { received: false });
  await changed(() => setCommit(fx.set_storage, baseRef, snap.guard));
  assert.deepEqual(await start(operation.call_token), { started: true });
  assert.deepEqual(await start(operation.call_token), { started: false });
  const inFlight = await reserve();
  assert.equal(inFlight.state, 'CALL_STARTED');
  assert.equal(inFlight.call_token, null);
  assert.equal(inFlight.material, null);
  assert.deepEqual(await receive(operation.call_token, fx.provider_receipt), { received: true });
  assert.deepEqual(await receive(operation.call_token, fx.provider_receipt), { received: true });
  await conflict(() => receive(operation.call_token, {
    ...fx.provider_receipt, raw: fx.provider_receipt.raw + '\n',
  }));
  const received = await reserve();
  assert.equal(received.state, 'RECEIVED');
  assert.equal(received.operation_id, operation.operation_id);
  assert.equal(received.call_token, null);
  assert.deepEqual(received.material, fx.operation_material);
  assert.deepEqual(received.receipt, fx.provider_receipt);
  assert.deepEqual(await fail(operation.call_token), { failed: false });
  const otherReceipt = structuredClone(fx.set_storage);
  otherReceipt.model_receipt = { ...fx.provider_receipt, raw: fx.provider_receipt.raw + '\n' };
  await assert.rejects(() => setCommit(otherReceipt, baseRef, snap.guard), error => error.code === '22023');
  assert.equal(await setCommit(fx.set_storage, baseRef, snap.guard), setId);
  const completed = await reserve();
  assert.equal(completed.state, 'COMPLETED');
  assert.equal(completed.artifact_id, setId);
  assert.equal(completed.call_token, null);
  assert.equal(completed.material, null);
  assert.equal(completed.receipt, null);
  assert.equal(await value(`select operation_material is null and provider_receipt is null
    and base_projection is null and base_private_evidence is null and call_token is null as v
    from public.analysis_if_scenario_sets where id=$1`, [setId]), true);
  assert.equal(await intentCommit(fx.saved_storage, setRef), savedId);
  const storedSet = await read('scenario_set', setId);
  const storedIntent = await read('saved_intent', savedId);
  assert.equal(storedSet.subscription_tier, 'premium');
  assert.equal(storedSet.items.length, 1);
  assert.equal(storedIntent.items.length, 1);
  assert.deepEqual(storedSet.items[0].storage, fx.set_storage);
  assert.deepEqual(storedIntent.items[0].storage, fx.saved_storage);
  assert.equal(storedIntent.items[0].storage.bundle.primary_artifact.selected_scenario_ref, chosen);
  for (const [table, id] of [['analysis_if_scenario_sets', setId], ['analysis_saved_route_intents', savedId]]) {
    await db.query(`update public.${table} set storage=storage where id=$1`, [id]);
    await conflict(() => db.query(`update public.${table} set storage=storage || '{"content_text":"changed"}'::jsonb where id=$1`, [id]));
  }

  // Replays keep the exact identity/bytes and a changed request cannot reuse a key.
  assert.equal(await setCommit(fx.set_storage, baseRef, snap.guard), setId);
  assert.equal(await intentCommit(fx.saved_storage, setRef), savedId);
  await conflict(() => setCommit(fx.set_storage, baseRef, snap.guard, { request: differentRequest }));
  await conflict(() => intentCommit(fx.saved_storage, setRef, { request: differentRequest }));
  await conflict(() => read('scenario_set', null, { key: setKey, request: differentRequest }));
  await conflict(() => read('saved_intent', null, { key: savedKey, request: differentRequest }));
  assert.equal((await read('scenario_set', null, { key: setKey, request: setRequest })).items[0].id, setId);
  assert.equal((await read('saved_intent', null, { key: savedKey, request: savedRequest })).items[0].id, savedId);
  assert.equal(await value('select count(*)::int as v from public.analysis_if_scenario_sets'), 1);
  assert.equal(await value('select count(*)::int as v from public.analysis_saved_route_intents'), 1);

  // A failed call and a deleted in-flight call never return a second call token.
  const failedKey = hash('failed-if-operation');
  const failedOp = await reserve({ key: failedKey, baseRef, guard: snap.guard, material: fx.operation_material });
  assert.deepEqual(await start(failedOp.call_token, failedKey), { started: true });
  assert.deepEqual(await fail(failedOp.call_token, failedKey), { failed: true });
  const failedAgain = await reserve({ key: failedKey });
  assert.equal(failedAgain.state, 'FAILED');
  assert.equal(failedAgain.call_token, null);
  assert.equal(failedAgain.material, null);
  assert.deepEqual(await start(failedOp.call_token, failedKey), { started: false });
  const deletedKey = hash('deleted-in-flight-if-operation');
  const deletedOp = await reserve({ key: deletedKey, baseRef, guard: snap.guard, material: fx.operation_material });
  assert.deepEqual(await start(deletedOp.call_token, deletedKey), { started: true });
  await remove('scenario_set', deletedOp.operation_id);
  await unavailable(() => reserve({ key: deletedKey }));
  await unavailable(() => start(deletedOp.call_token, deletedKey));
  await unavailable(() => receive(deletedOp.call_token, fx.provider_receipt, deletedKey));
  const sourceDeleteKey = hash('received-before-source-delete');
  const sourceDeleteOp = await reserve({ key: sourceDeleteKey, baseRef, guard: snap.guard, material: fx.operation_material });
  await start(sourceDeleteOp.call_token, sourceDeleteKey);
  await receive(sourceDeleteOp.call_token, fx.provider_receipt, sourceDeleteKey);
  assert.equal((await read('scenario_set')).items.length, 1);

  await unavailable(() => context(baseRef, other));
  assert.equal((await read('scenario_set', setId, { user: other })).items.length, 0);
  assert.equal((await read('saved_intent', savedId, { user: other })).items.length, 0);
  await unavailable(() => setCommit(fx.set_storage, baseRef, snap.guard, { user: other }));
  await unavailable(() => intentCommit(fx.saved_storage, setRef, { user: other }));
  await unavailable(() => remove('scenario_set', setId, other));
  await unavailable(() => remove('saved_intent', savedId, other));
  assert.equal(await reserve({ user: other }), null);
  await unavailable(() => start(sourceDeleteOp.call_token, sourceDeleteKey, other));
  await unavailable(() => receive(sourceDeleteOp.call_token, fx.provider_receipt, sourceDeleteKey, other));
  assert.equal((await read('saved_intent', savedId)).items.length, 1);

  // Current entitlement is checked on reads and writes, including replay paths.
  for (const plan of ['free', 'plus']) {
    await tier(plan);
    await denied(() => context(baseRef));
    await denied(() => read('scenario_set', setId));
    await denied(() => read('saved_intent', savedId));
    await denied(() => setCommit(fx.set_storage, baseRef, snap.guard));
    await denied(() => intentCommit(fx.saved_storage, setRef));
    await denied(() => reserve());
    await denied(() => start(sourceDeleteOp.call_token, sourceDeleteKey));
    await denied(() => receive(sourceDeleteOp.call_token, fx.provider_receipt, sourceDeleteKey));
    await denied(() => fail(sourceDeleteOp.call_token, sourceDeleteKey));
  }
  await tier('premium');
  for (const role of ['anon', 'authenticated']) {
    await db.exec('set role ' + role);
    await denied(() => db.query('select * from public.analysis_if_scenario_sets'));
    await denied(() => db.query('select * from public.analysis_saved_route_intents'));
    await denied(() => context(baseRef));
    await denied(() => read('scenario_set', setId));
    await denied(() => read('saved_intent', savedId));
    await denied(() => setCommit(fx.set_storage, baseRef, snap.guard));
    await denied(() => intentCommit(fx.saved_storage, setRef));
    await denied(() => remove('scenario_set', setId));
    await denied(() => remove('saved_intent', savedId));
    await denied(() => reserve());
    await denied(() => start(sourceDeleteOp.call_token, sourceDeleteKey));
    await denied(() => receive(sourceDeleteOp.call_token, fx.provider_receipt, sourceDeleteKey));
    await denied(() => fail(sourceDeleteOp.call_token, sourceDeleteKey));
    await db.exec('reset role');
    await db.exec('set role service_role');
  }

  // Additional input changes the current-map guard but not this saved base cohort.
  const added = { ...snap.members[0].original, id: addedId, memo: '私は散歩に出かけた。' };
  await admin('insert into public.emotions values($1,$2,$3,$4,$5,$6,$7,$8)', [
    added.id, owner, added.created_at, added.memo, added.memo_action, added.category, added.emotions, added.emotion_details,
  ]);
  assert.notEqual((await snapshot()).guard, snap.guard);
  assert.equal((await read('scenario_set', setId)).items.length, 1);
  assert.equal((await read('saved_intent', savedId)).items.length, 1);
  // The mutable current-map cache may prune its row; saved IF/Saved snapshots survive.
  await admin('delete from public.analysis_observed_artifacts where id=$1', [baseId]);
  assert.equal((await read('scenario_set', setId)).items.length, 1);
  assert.equal((await read('saved_intent', savedId)).items.length, 1);
  assert.deepEqual((await read('saved_intent', savedId)).items[0].storage, fx.saved_storage);
  const resumedAfterPrune = await reserve({ key: sourceDeleteKey });
  assert.equal(resumedAfterPrune.state, 'RECEIVED');
  assert.equal(resumedAfterPrune.call_token, null);
  assert.deepEqual(resumedAfterPrune.material, fx.operation_material);
  assert.deepEqual(resumedAfterPrune.receipt, fx.provider_receipt);

  // Editing one dependency blocks stored reads and both kinds of commit replay.
  const original = snap.members[0].original;
  await admin('update public.emotions set memo=$1 where id=$2', ['私は仕事を続けなかった。', original.id]);
  assert.equal((await read('scenario_set', setId)).items.length, 0);
  assert.equal((await read('saved_intent', savedId)).items.length, 0);
  await changed(() => read('scenario_set', null, { key: setKey, request: setRequest }));
  await changed(() => setCommit(fx.set_storage, baseRef, snap.guard));
  await changed(() => intentCommit(fx.saved_storage, setRef));
  await changed(() => reserve({ key: sourceDeleteKey }));
  // Restore only this synthetic edit, so deletion is tested independently.
  await admin('update public.emotions set memo=$1 where id=$2', [original.memo, original.id]);
  assert.equal((await read('saved_intent', savedId)).items.length, 1);
  await admin('delete from public.emotions where id=$1', [original.id]);
  assert.equal((await read('scenario_set', setId)).items.length, 0);
  assert.equal((await read('saved_intent', savedId)).items.length, 0);
  // Source deletion removes the derivative private bodies, not just read access.
  assert.equal(await value('select storage is null and deleted_at is not null as v from public.analysis_if_scenario_sets where id=$1', [setId]), true);
  assert.equal(await value('select storage is null and deleted_at is not null as v from public.analysis_saved_route_intents where id=$1', [savedId]), true);
  assert.equal(await value(`select operation_material is null and provider_receipt is null
    and base_projection is null and base_private_evidence is null and call_token is null and deleted_at is not null as v
    from public.analysis_if_scenario_sets where id=$1`, [sourceDeleteOp.operation_id]), true);
  await unavailable(() => receive(sourceDeleteOp.call_token, fx.provider_receipt, sourceDeleteKey));

  // Downgrade/source loss cannot trap a person's private data: deletion stays allowed.
  await tier('free');
  assert.deepEqual(await remove('saved_intent', savedId), { deleted: true, id: savedId });
  assert.deepEqual(await remove('scenario_set', setId), { deleted: true, id: setId });
  assert.equal(await value('select storage is null and deleted_at is not null as v from public.analysis_if_scenario_sets where id=$1', [setId]), true);
  assert.equal(await value('select storage is null and deleted_at is not null as v from public.analysis_saved_route_intents where id=$1', [savedId]), true);
  await tier('premium');
  await unavailable(() => read('scenario_set', null, { key: setKey, request: setRequest }));
  await unavailable(() => read('saved_intent', null, { key: savedKey, request: savedRequest }));
  await conflict(() => setCommit(fx.set_storage, baseRef, snap.guard));
  for (const [table, id] of [['analysis_if_scenario_sets', setId], ['analysis_saved_route_intents', savedId]]) {
    await conflict(() => db.query(`update public.${table} set deleted_at=null where id=$1`, [id]));
  }

  // The remaining operation identities also leave with the account.
  await admin('delete from auth.users where id=$1', [owner]);
  assert.equal(await value('select count(*)::int as v from public.analysis_if_scenario_sets'), 0);
  assert.equal(await value('select count(*)::int as v from public.analysis_saved_route_intents'), 0);
  console.log(JSON.stringify({ status: 'passed', sourceRecords: snap.members.length,
    scope: 'IF/Saved SQL: durable single-call reservation/receipt, immutable saved bytes, replay, ownership, entitlement, source fences, prune survival, deletion, ACL' }));
}

run().catch(error => {
  console.error({ message: error.message, code: error.code, position: error.position, where: error.where });
  process.exitCode = 1;
}).finally(() => db.close());
