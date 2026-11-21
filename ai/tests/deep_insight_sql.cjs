// Load the actual source relations and the DeepInsight migration in an empty,
// isolated PostgreSQL runtime. No external data, service or model is used.
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { PGlite } = require(process.env.Q2_PGLITE_MODULE);

const root = path.resolve(__dirname, '../..');
const db = new PGlite();
const free = '00000000-0000-0000-0000-000000000001';
const plus = '00000000-0000-0000-0000-000000000002';
const premium = '00000000-0000-0000-0000-000000000003';
const recordId = '00000000-0000-0000-0000-000000000004';
const threadId = '00000000-0000-0000-0000-000000000005';
const questionEventId = '00000000-0000-0000-0000-000000000006';
const answerEventId = '00000000-0000-0000-0000-000000000007';
const mapId = '00000000-0000-0000-0000-000000000008';
const sha256 = (s) => createHash('sha256').update(s).digest('hex');
const value = async (sql, args = []) => (await db.query(sql, args)).rows[0].v;
const state = (user) => value('select public.deep_insight_state($1) as v', [user]);
const context = (user) => value('select public.deep_insight_candidate_context($1) as v', [user]);
const themeContext = (user, theme) => value('select public.deep_insight_theme_candidate_context($1,$2) as v', [user, theme]);
const issue = async (user, lane, key, { day, guard, theme = '人間関係' } = {}) => value(
  'select public.deep_insight_issue($1,$2,$3,$4,$5,$6,$7,$8) as v',
  [user, day ?? (await state(user)).day, lane, lane === 'theme' ? theme : null,
    '大切にしていることは何ですか？ ' + key, key, 'question-' + key, guard ?? (await context(user)).guard]);
const answer = (user, row, text) => value('select public.deep_insight_answer($1,$2,$3) as v', [user, row.id, text]);
const fail = (code, run) => assert.rejects(run, error => error.code === code);

const groundedIssue = async (user, receipt, { day, guard, theme = '人間関係' } = {}) => value(
  'select public.deep_insight_issue_grounded($1,$2,$3,$4,$5,$6,$7,$8,$9) as v',
  [user, day ?? (await state(user)).day, receipt.lane, receipt.lane === 'theme' ? theme : null,
    '大切にしていることは何ですか？', 'deep-insight-target-' + receipt.target_key,
    'question-' + receipt.target_key, guard ?? (await context(user)).guard, JSON.stringify(receipt)]);

function receipt(source, field, text, start, end) {
  return {
    policy_version: 'deep-insight.v2', lane: 'records', focus: 'CONDITION',
    source_id: source.id, source_version: source.source_version, field, start, end,
    literal_sha256: sha256([...text].slice(start, end).join('')),
    condition_key: sha256('condition'), target_key: sha256('target-' + source.id),
  };
}

async function verifyThemeNotifications() {
  const freeUser = '00000000-0000-0000-0000-000000000011';
  const paidUser = '00000000-0000-0000-0000-000000000012';
  const alerts = () => value('select public.deep_insight_theme_notification_enqueue_due() as v');
  const preference = (user, enabled) => value(
    'select public.deep_insight_theme_notification_write($1,$2) as v', [user, enabled]);
  const claim = (user, question) => value(
    'select public.deep_insight_theme_notification_can_send($1,$2) as v', [user, question]);
  const seed = (user, age, key) => value(`insert into public.deep_insight_questions
    (user_id,lane,theme,question_text,issued_on,issued_at,question_key,text_key)
    values($1,'theme','人間関係','個人情報を含めない問い',((now()-$2::interval) at time zone 'Asia/Tokyo')::date,
      now()-$2::interval,$3,$3) returning id as v`, [user, age, key]);
  const changeTier = (tier) => db.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, paidUser]);
  const job = (question) => value('select to_jsonb(j) as v from public.astor_jobs j where job_key=$1',
    ['deep_insight_theme_ready:' + question]);

  await db.exec('reset role');
  await db.query('insert into auth.users values($1),($2)', [freeUser, paidUser]);
  await db.query(`insert into public.profiles(id,subscription_tier,push_enabled,push_token)
    values($1,'free',true,'free-device'),($2,'plus',true,'paid-device')`, [freeUser, paidUser]);
  const priorFreeQuestion = await seed(freeUser, '200 hours', 'prior-free-notification');
  const freeQuestion = await seed(freeUser, '167 hours', 'free-notification');
  const paidQuestion = await seed(paidUser, '25 hours', 'paid-notification');
  await db.exec('set role service_role');

  assert.equal((await state(paidUser)).theme_notification_enabled, false);
  assert.deepEqual(await alerts(), {queued: 0});
  assert.deepEqual(await preference(paidUser, true), {enabled: true});
  assert.deepEqual(await preference(freeUser, true), {enabled: true});
  assert.equal((await state(paidUser)).theme_notification_enabled, true);
  assert.deepEqual(await alerts(), {queued: 1});
  assert.deepEqual(await alerts(), {queued: 0});
  const queued = await job(paidQuestion);
  assert.deepEqual(queued.payload.data, {
    type: 'deep_insight_theme_ready', target: 'deep_insight', user_id: paidUser, question_id: paidQuestion,
  });
  assert.equal(JSON.stringify(queued.payload).includes('個人情報を含めない問い'), false);
  assert.deepEqual(await claim(freeUser, paidQuestion), {eligible: false});
  assert.deepEqual(await claim(freeUser, priorFreeQuestion), {eligible: false});

  await changeTier('free');
  const deferred = await claim(paidUser, paidQuestion);
  assert.equal(deferred.eligible, false);
  assert.equal(deferred.defer_until, (await state(paidUser)).theme_next_available_at);
  await db.query('update public.astor_jobs set run_after=$1 where job_key=$2', [deferred.defer_until, queued.job_key]);
  assert.deepEqual(await alerts(), {queued: 0});
  await changeTier('premium');
  assert.deepEqual(await alerts(), {queued: 1});
  assert.ok(Date.parse((await job(paidQuestion)).run_after) < Date.parse(deferred.defer_until));
  assert.equal((await job(paidQuestion)).job_key, queued.job_key);

  await preference(paidUser, false);
  assert.deepEqual(await claim(paidUser, paidQuestion), {eligible: false});
  await preference(paidUser, true);
  await db.query('update public.profiles set push_enabled=false where id=$1', [paidUser]);
  assert.deepEqual(await claim(paidUser, paidQuestion), {eligible: false});
  await db.query('update public.profiles set push_enabled=true where id=$1', [paidUser]);
  assert.deepEqual(await claim(paidUser, paidQuestion), {eligible: true});
  assert.deepEqual(await claim(paidUser, paidQuestion), {eligible: false});
  await db.query('delete from public.astor_jobs where job_key=$1', [queued.job_key]);
  assert.deepEqual(await alerts(), {queued: 0});

  await db.exec('reset role');
  await db.query(`update public.deep_insight_questions set issued_at=now()-interval '169 hours',
    issued_on=((now()-interval '169 hours') at time zone 'Asia/Tokyo')::date where id=$1`, [freeQuestion]);
  await db.exec('set role service_role');
  assert.deepEqual(await alerts(), {queued: 1});
  assert.equal((await job(freeQuestion)).user_id, freeUser);
  assert.equal((await issue(freeUser, 'theme', 'replacement-notification')).status, 'issued');
  assert.deepEqual(await claim(freeUser, freeQuestion), {eligible: false});
  assert.deepEqual(await alerts(), {queued: 0});
}

async function verifyThemePrivacyAndRecordsPlan(themeGrounding) {
  const owner = '00000000-0000-0000-0000-000000000013';
  const other = '00000000-0000-0000-0000-000000000014';
  const selected = '人間関係';
  const different = '仕事・学び';

  await db.exec('reset role');
  await db.query('insert into auth.users values($1),($2)', [owner, other]);
  await db.query("insert into public.profiles(id,subscription_tier) values($1,'plus'),($2,'free')", [owner, other]);
  await db.query(`insert into public.emotions(id,user_id,created_at,memo,memo_action)
    values(gen_random_uuid(),$1,now() at time zone 'UTC' - interval '1 minute','個人の思考','個人の行動')`, [owner]);
  await db.query(`insert into public.deep_insight_questions
    (user_id,lane,theme,question_text,issued_on,issued_at,question_key,text_key)
    select $1,'theme',$2,'既出の問い '||n,((now()-make_interval(days=>n+10)) at time zone 'Asia/Tokyo')::date,
      now()-make_interval(days=>n+10),'prior-question-'||n,'prior-text-'||n from generate_series(1,34) n`, [owner, selected]);
  const firstHistoryId = await value(`select id as v from public.deep_insight_questions
    where user_id=$1 and question_key='prior-question-1'`, [owner]);
  const seedOtherTheme = (user, theme) => db.query(`insert into public.deep_insight_questions
    (user_id,lane,theme,question_text,issued_on,issued_at,question_key,text_key,answer_text,answered_at)
    values($1,'theme',$2,'範囲外の問い',((now()-interval '9 days') at time zone 'Asia/Tokyo')::date,
      now()-interval '9 days','other-theme-question','other-theme-text','範囲外の回答',now()-interval '9 days')`, [user, theme]);
  await seedOtherTheme(owner, different);
  await seedOtherTheme(other, selected);
  await db.exec('set role service_role');
  assert.equal((await state(owner)).can_use_records, true);
  const pending = (await issue(owner, 'records', 'old-records')).question;
  assert.ok(pending);

  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations',
    '20261121190000_deep_insight_theme_candidate_context.sql'), 'utf8'));
  await db.exec('set role service_role');

  const narrow = await themeContext(owner, selected);
  assert.match(narrow.guard, /^deep-insight-theme-v1:[0-9a-f]{64}$/);
  assert.deepEqual(Object.keys(narrow.material), ['questions']);
  assert.equal(narrow.material.questions.length, 34);
  narrow.material.questions.forEach((question, index) => {
    const n = index + 1;
    assert.deepEqual(question, {
      question_key: `prior-question-${n}`,
      text_key: `prior-text-${n}`,
      ...(n <= 30 ? {question_text: `既出の問い ${n}`} : {}),
    });
  });
  assert.notEqual((await themeContext(other, selected)).guard, narrow.guard);
  assert.notEqual((await themeContext(owner, different)).guard, narrow.guard);
  assert.deepEqual((await themeContext(other, different)).material, {questions: []});

  assert.equal((await state(owner)).can_use_records, false);
  assert.equal((await state(owner)).record_available_today, false);
  assert.equal((await state(owner)).records.id, pending.id);
  assert.equal((await issue(owner, 'records', 'old-record-retry')).question.id, pending.id);
  const saved = await answer(owner, pending, '記録への本人回答');
  await answer(owner, {id: firstHistoryId}, '個人の過去回答');
  assert.deepEqual(await themeContext(owner, selected), narrow);
  assert.ok((await state(owner)).history.some((question) => question.id === pending.id));
  const snapshot = await value("select public.analysis_cumulative_source_snapshot($1)->'members' as v", [owner]);
  assert.ok(snapshot.some((member) => member.original.id === pending.id
    && member.original.memo === saved.question.answer_text));
  await assert.rejects(() => issue(owner, 'records', 'new-plus-record'),
    {code: '42501', message: 'deep_insight_records_locked'});
  assert.equal((await state(premium)).can_use_records, true);

  assert.equal((await groundedIssue(owner, themeGrounding, {theme: different, guard: narrow.guard})).status, 'no_question');
  await db.query(`insert into public.deep_insight_questions
    (user_id,lane,theme,question_text,issued_on,issued_at,question_key,text_key)
    values($1,'theme',$2,'以前に発行した問い',((now()-interval '50 days') at time zone 'Asia/Tokyo')::date,
      now()-interval '50 days','prior-question-35','prior-text-35')`, [owner, selected]);
  assert.equal((await groundedIssue(owner, themeGrounding, {guard: narrow.guard})).status, 'no_question');
  const refreshed = await themeContext(owner, selected);
  assert.equal((await issue(owner, 'theme', 'prior-question-34', {guard: refreshed.guard})).status, 'no_question');
  const issued = await groundedIssue(owner, themeGrounding, {guard: refreshed.guard});
  assert.equal(issued.status, 'issued');
  assert.equal(issued.question.theme, selected);
  assert.equal((await state(owner)).theme_next_available_at, issued.theme_next_available_at);
  assert.notEqual((await themeContext(owner, selected)).guard, refreshed.guard);

  // The deployed pre-transition API can still use its original material guard.
  assert.equal((await groundedIssue(other, themeGrounding)).status, 'issued');
}

async function verifyRecordsNotifications() {
  const memo = '記録に残した本人の判断';
  async function seedUser(pushEnabled, token) {
    await db.exec('reset role');
    const user = await value('insert into auth.users values(gen_random_uuid()) returning id as v');
    await db.query(`insert into public.profiles(id,subscription_tier,push_enabled,push_token)
      values($1,'premium',$2,$3)`, [user, pushEnabled, token]);
    await db.query(`insert into public.emotions(id,user_id,created_at,memo,memo_action)
      values(gen_random_uuid(),$1,now() at time zone 'UTC' - interval '1 minute',$2,'')`, [user, memo]);
    await db.exec('set role service_role');
    return user;
  }
  async function issueRecord(user, guard) {
    const source = (await context(user)).material.records[0];
    return groundedIssue(user, receipt(source, 'thought', memo, 0, [...memo].length), {guard});
  }
  const claim = (user, id) => value('select public.deep_insight_record_notification_can_send($1,$2) as v', [user, id]);
  const jobRows = async (user) => (await db.query(`select job_key,job_type,user_id,payload
    from public.astor_jobs where user_id=$1 and job_key like 'deep_insight_record_ready:%'`, [user])).rows;

  const owner = await seedUser(true, 'synthetic-device');
  assert.equal((await issueRecord(owner, 'stale-guard')).status, 'no_question');
  assert.deepEqual(await jobRows(owner), []);
  const outcome = await issueRecord(owner);
  assert.equal(outcome.status, 'issued');
  const question = outcome.question;
  assert.equal((await issueRecord(owner)).question.id, question.id);
  const [job] = await jobRows(owner);
  assert.equal((await jobRows(owner)).length, 1);
  assert.equal(job.job_type, 'send_fcm_push_v1');
  assert.equal(job.job_key, 'deep_insight_record_ready:' + question.id);
  assert.deepEqual(job.payload.recipient_user_ids, [owner]);
  assert.deepEqual(job.payload.data, {
    type: 'deep_insight_record_ready', target: 'deep_insight', user_id: owner, question_id: question.id,
  });
  assert.equal(JSON.stringify(job.payload).includes(question.question_text), false);
  assert.equal(JSON.stringify(job.payload).includes(memo), false);
  assert.deepEqual(await claim(free, question.id), {eligible: false});

  await db.query("update public.profiles set subscription_tier='plus' where id=$1", [owner]);
  assert.deepEqual(await claim(owner, question.id), {eligible: false});
  await db.query("update public.profiles set subscription_tier='premium',push_enabled=false where id=$1", [owner]);
  assert.deepEqual(await claim(owner, question.id), {eligible: false});
  await db.query('update public.profiles set push_enabled=true where id=$1', [owner]);
  assert.deepEqual(await claim(owner, question.id), {eligible: true});
  assert.deepEqual(await claim(owner, question.id), {eligible: false});

  const answeredOwner = await seedUser(true, 'synthetic-second-device');
  const answered = (await issueRecord(answeredOwner)).question;
  assert.equal((await answer(answeredOwner, answered, '本人の回答')).inserted, true);
  assert.equal((await jobRows(answeredOwner)).length, 1);
  assert.deepEqual(await claim(answeredOwner, answered.id), {eligible: false});

  const disabled = await seedUser(false, 'synthetic-disabled-device');
  assert.equal((await issueRecord(disabled)).status, 'issued');
  assert.deepEqual(await jobRows(disabled), []);

  const noDevice = await seedUser(true, null);
  assert.equal((await issueRecord(noDevice)).status, 'issued');
  assert.deepEqual(await jobRows(noDevice), []);

  const ungroundedOwner = await seedUser(true, 'synthetic-third-device');
  assert.equal((await issue(ungroundedOwner, 'records', 'no-grounding')).status, 'issued');
  assert.deepEqual(await jobRows(ungroundedOwner), []);
}

async function verifyRecordAssessmentAfterMap() {
  async function seed(tier) {
    await db.exec('reset role');
    const owner = await value('insert into auth.users values(gen_random_uuid()) returning id as v');
    await db.query('insert into public.profiles(id,subscription_tier) values($1,$2)', [owner, tier]);
    await db.query(`insert into public.emotions(id,user_id,created_at,memo,memo_action)
      values(gen_random_uuid(),$1,now() at time zone 'UTC' - interval '1 minute','本人の記録','')`, [owner]);
    await db.exec('set role service_role');
    return owner;
  }
  async function saveMap(owner) {
    // Give separate saves distinct statement times in the WASM database.
    await new Promise((resolve) => setTimeout(resolve, 3));
    const id = await value("select 'artifact:'||replace(gen_random_uuid()::text,'-','') as v");
    const projection = {wire_kind: 'watashi.map.v2', projection_of: id + '@1'};
    const saved = await value(`with source as materialized (select public.analysis_cumulative_source_snapshot($1) as s)
      select jsonb_build_object('guard',s->>'guard','report',public.analysis_cumulative_commit($1,s->>'guard',$2,
        jsonb_build_object('schema_version','analysis.private-evidence.v1','projection_of',$2||'@1',
          'coverage',jsonb_build_object('profile','cumulative.v1','source_count',jsonb_array_length(s->'members'))),
        $3,'試験用のマップ',(s->>'period_start')::timestamptz,(s->>'period_end')::timestamptz,null,true)) as v
      from source`, [owner, id, JSON.stringify(projection)]);
    assert.equal(saved.report.replaceAll('-', ''), id.slice('artifact:'.length));
    return saved;
  }
  const job = (owner) => value(`select (select to_jsonb(j) from public.astor_jobs j
    where j.job_key='deep_insight_records_assessment:'||$1::uuid::text) as v`, [owner]);
  const claim = async (owner, attempts) => {
    await db.query(`update public.astor_jobs set status='running',attempts=$2,worker_id='test-worker',
      started_at=clock_timestamp(),updated_at=clock_timestamp()
      where job_key='deep_insight_records_assessment:'||$1::uuid::text`, [owner, attempts]);
    return job(owner);
  };
  const settle = (original, retry, worker = original.worker_id) => value('select public.deep_insight_record_assessment_settle($1,$2,$3,$4,$5) as v',
    [original.job_key, worker, original.started_at, original.updated_at, retry]);

  for (const tier of ['free', 'plus']) {
    const owner = await seed(tier);
    await saveMap(owner);
    assert.equal(await job(owner), null);
  }

  const owner = await seed('premium');
  const first = await saveMap(owner);
  const pending = await job(owner);
  assert.equal(pending.status, 'queued');
  assert.equal(pending.job_type, 'deep_insight_records_assessment_v1');
  assert.deepEqual(pending.payload, {source_guard: first.guard});
  assert.equal(pending.max_attempts, 3);
  assert.equal((await context(owner)).material.map.source_version, sha256(first.guard));
  const replay = await saveMap(owner);
  assert.notEqual(replay.report, first.report);
  assert.equal(replay.guard, first.guard);
  assert.deepEqual(await job(owner), pending);

  const priorClaim = await claim(owner, 3);
  await db.query("update public.emotions set memo='本人の新しい記録' where user_id=$1", [owner]);
  const newer = await saveMap(owner);
  const coalesced = await job(owner);
  assert.notEqual(newer.guard, first.guard);
  assert.deepEqual(coalesced.payload, {source_guard: newer.guard});
  assert.equal(coalesced.status, 'running');
  assert.equal(coalesced.started_at, priorClaim.started_at);
  assert.deepEqual(await settle(priorClaim, true, 'another-worker'), {settled: false});
  assert.deepEqual(await settle(priorClaim, true), {settled: true});
  assert.equal((await job(owner)).status, 'queued');
  assert.equal((await job(owner)).attempts, 0);

  const retryable = await claim(owner, 1);
  assert.deepEqual(await settle(retryable, true), {settled: true});
  const retry = await job(owner);
  assert.equal(retry.status, 'queued');
  assert.ok(Date.parse(retry.run_after) > Date.parse(retry.updated_at));
  assert.equal(retry.attempts, 1);
  assert.deepEqual(await settle(retryable, false), {settled: false});

  assert.deepEqual(await settle(await claim(owner, 3), true), {settled: true});
  const failed = await job(owner);
  assert.equal(failed.status, 'failed');
  await saveMap(owner);
  assert.deepEqual(await job(owner), failed);

  await db.query("update public.profiles set push_token='synthetic-device' where id=$1", [owner]);
  const current = await context(owner);
  const source = current.material.records[0];
  const grounded = receipt(source, 'thought', source.thought, 0, [...source.thought].length);
  const question = (await groundedIssue(owner, grounded, {guard: current.guard})).question;
  assert.ok(question);
  assert.equal(await value('select job_type as v from public.astor_jobs where job_key=$1',
    ['deep_insight_record_ready:' + question.id]), 'send_fcm_push_v1');
  await db.query("update public.emotions set memo='次の記録' where user_id=$1", [owner]);
  await saveMap(owner);
  assert.deepEqual(await job(owner), failed);
  await answer(owner, question, '本人の回答');
  await saveMap(owner);
  assert.deepEqual(await job(owner), failed);
}

async function run() {
  await db.exec(`create role anon; create role authenticated; create role service_role bypassrls;
    create schema auth; create table auth.users(id uuid primary key);
    create table public.profiles(id uuid primary key references auth.users(id) on delete cascade,subscription_tier text,
      push_enabled boolean default true,push_token text);
    create table public.emotions(id uuid primary key,user_id uuid references auth.users(id) on delete cascade,
      created_at timestamp,memo text,memo_action text,category text[],emotions text[],emotion_details jsonb);
    create table public.astor_jobs(job_key text primary key,job_type text,user_id uuid,payload jsonb,priority integer,
      run_after timestamptz,updated_at timestamptz default now(),status text default 'queued',
      attempts integer default 0,max_attempts integer default 8,worker_id text,started_at timestamptz,
      finished_at timestamptz,last_error text);
    grant usage on schema public to anon,authenticated,service_role;
    grant all on public.profiles,public.emotions,public.astor_jobs to service_role;`);
  for (const file of [
    '20260911020509_emlis_input_threads_q2.sql',
    '20260911041749_emlis_q3_plan_rounds.sql',
    '20261003134440_analysis_observed_artifacts.sql',
    '20261004041627_analysis_period_comparison.sql',
    '20261101010000_emlis_natural_related_context.sql',
    '20261101080144_cumulative_watashi_map.sql',
    '20261107071033_analysis_semantic_map_wire.sql',
    '20261114032520_analysis_interpretation_correction_sources.sql',
    '20261114120000_analysis_if_route_artifacts.sql',
    '20261114123000_analysis_emlis_material_handoff.sql',
    '20261114132000_analysis_map_interpretation_corrections.sql',
    '20261114133000_analysis_map_correction_handoff.sql',
    '20261121132000_deep_insight_questions.sql',
    '20261121133000_analysis_deep_insight_answer_handoff.sql',
    '20261121134000_deep_insight_grounded_questions.sql',
  ]) await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations', file), 'utf8'));

  await db.query('insert into auth.users values($1),($2),($3)', [free, plus, premium]);
  await db.query("insert into public.profiles(id,subscription_tier) values($1,'free'),($2,'plus'),($3,'premium')",
    [free, plus, premium]);
  await db.query("insert into public.emotions values($1,$2,now() at time zone 'UTC' - interval '1 minute','🧪本人の記録',null,null,null,null)",
    [recordId, free]);
  await db.query(`insert into public.emlis_input_threads(id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
    select $1,e.user_id,e.id,1,'AWAITING_ANSWER',1,public.emlis_parent_source(e),
      '{"original_source_ref":"original","body_state":"PRE_QUESTION"}'::jsonb
    from public.emotions e where e.id=$2`, [threadId, recordId]);
  await db.query(`insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,payload)
    values($1,$2,1,'QUESTION',1,'emlis-question','{"original_source_ref":"original","prompt_private":"なぜですか？"}')`,
    [questionEventId, threadId]);
  await db.exec('set role service_role');
  assert.equal((await state(free)).can_use_theme, false);
  assert.deepEqual((await context(plus)).material.records, []);
  let original = (await context(free)).material.records[0];
  assert.equal(original.thought, '🧪本人の記録');
  assert.equal(original.emlis_open_question_id, 'emlis-question');
  assert.equal(original.emlis_open_question, 'なぜですか？');
  assert.match(original.source_version, /^[0-9a-f]{64}$/);
  await db.query("update public.emlis_input_threads set state='COMPLETED' where id=$1", [threadId]);
  assert.equal((await context(free)).material.records[0].emlis_open_question, null);
  await db.query(`insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,question_id,payload)
    values($1,$2,2,'ANSWER',1,'emlis-question',$3)`, [answerEventId, threadId,
    JSON.stringify({ source: { answer_id: answerEventId, thread_id: threadId, question_id: 'emlis-question',
      round_index: 1, original_source_ref: 'original', answer_text_private: '本人が答えた材料',
      source_role: 'SUPPLEMENTAL_ANSWER', source_version: 'cocolon.cmee.supplemental_answer.v1' } })]);
  original = (await context(free)).material.records[0];
  const emlisAnswer = original.emlis_answered_questions[0];
  assert.equal(emlisAnswer.id, answerEventId);
  assert.equal(emlisAnswer.question_id, 'emlis-question');
  assert.ok(Number.isFinite(Date.parse(emlisAnswer.answered_at)));
  assert.match(emlisAnswer.source_version, /^[0-9a-f]{64}$/);
  assert.equal(emlisAnswer.answer, '本人が答えた材料');
  const mapGuard = await value("select public.analysis_cumulative_source_snapshot($1)->>'guard' as v", [free]);
  await db.query(`insert into public.analysis_observed_artifacts(id,artifact_id,artifact_version,user_id,
    report_type,report_mode,access_tier,period_start,period_end,source_guard,private_evidence,safe_projection,
    content_text,source_profile)
    values($1::uuid,'artifact:'||replace($1::uuid::text,'-',''),1,$2,'latest','standard','free',now()-interval '2 minutes',now(),$3,
      jsonb_build_object('schema_version','analysis.private-evidence.v1','projection_of','artifact:'||replace($1::uuid::text,'-','')||'@1'),
      jsonb_build_object('wire_kind','watashi.map.v2','projection_of','artifact:'||replace($1::uuid::text,'-','')||'@1'),
      '現在版の参考内容','cumulative.v1')`, [mapId, free, mapGuard]);
  assert.equal((await context(free)).material.map.id, mapId);
  assert.equal((await context(plus)).material.map, null);
  assert.match((await context(free)).material.map.source_version, /^[0-9a-f]{64}$/);
  await db.query(`insert into public.emlis_thread_events(id,thread_id,seq,kind,round_index,payload)
    values(gen_random_uuid(),$1,3,'OPERATION',1,'{"stage":"INTERPRETATION_CORRECTION"}')`, [threadId]);
  assert.deepEqual((await context(free)).material.records[0].emlis_answered_questions, []);
  assert.equal((await context(free)).material.map, null);
  await fail('42501', () => issue(free, 'theme', 'forbidden'));
  assert.equal((await issue(free, 'records', 'stale', { guard: 'incorrect' })).status, 'no_question');
  const grounding = receipt(original, 'thought', original.thought, 1, 6);
  await fail('22023', () => groundedIssue(free, { ...grounding, literal_sha256: sha256('不一致') }));
  await fail('22023', () => groundedIssue(free, { ...grounding, literal: original.thought }));
  await fail('22023', () => groundedIssue(plus, grounding));
  assert.equal((await groundedIssue(free, grounding, { guard: 'incorrect' })).status, 'no_question');
  const first = (await groundedIssue(free, grounding)).question;
  assert.equal(first.lane, 'records');
  assert.equal('grounding_receipt' in first, false);
  assert.deepEqual((await context(free)).material.prior[0].grounding_receipt, grounding);
  assert.equal((await groundedIssue(free, grounding)).status, 'existing');
  assert.deepEqual((await issue(free, 'records', 'concurrent')).question, first);
  assert.deepEqual((await state(free)).records, first);
  assert.equal((await state(free)).record_available_today, false);

  await fail('P0002', () => answer(plus, first, '別のユーザー'));
  const saved = await answer(free, first, ' 本人が答えた文。\n次の行。  ');
  assert.equal(saved.inserted, true);
  assert.deepEqual(await answer(free, first, saved.question.answer_text), { ...saved, inserted: false });
  await fail('23505', () => answer(free, first, '同じ問いへの異なる回答'));
  assert.deepEqual((await state(free)).history, [saved.question]);
  assert.equal((await issue(free, 'records', 'same-day')).status, 'daily_limit');
  assert.equal((await context(free)).material.prior[0].answer_text, saved.question.answer_text);

  const themeGrounding = {
    policy_version: 'deep-insight.v2', lane: 'theme', focus: 'RELATIONSHIP',
    source_id: null, source_version: null, field: null, start: null, end: null,
    literal_sha256: null, condition_key: null, target_key: sha256('theme-relationship'),
  };
  await fail('42501', () => groundedIssue(free, themeGrounding));
  await fail('22023', () => groundedIssue(plus, { ...themeGrounding, source_id: recordId }));
  const theme = (await groundedIssue(plus, themeGrounding)).question;
  assert.equal(theme.theme, '人間関係');
  assert.deepEqual((await context(plus)).material.prior[0].grounding_receipt, themeGrounding);
  assert.deepEqual((await issue(plus, 'theme', 'second-theme')).question, theme);
  assert.equal((await issue(plus, 'records', 'separate-lane')).status, 'issued');
  const pending = (await issue(premium, 'records', 'yesterday')).question;
  await db.exec('reset role');
  await db.query("update public.deep_insight_questions set issued_on=issued_on-1 where id=$1", [pending.id]);
  await db.exec('set role service_role');
  const acrossDays = (await state(premium)).records;
  assert.equal(acrossDays.id, pending.id);
  assert.notEqual(acrossDays.issued_on, pending.issued_on);
  assert.deepEqual((await issue(premium, 'records', 'another-day')).question, acrossDays);
  assert.equal((await issue(premium, 'theme', 'premium-theme')).status, 'issued');
  assert.equal((await answer(premium, acrossDays, '翌日の本人回答。')).inserted, true);
  const answeredPrior = (await context(premium)).material.prior.find((item) => item.id === acrossDays.id);
  const answerGrounding = receipt(answeredPrior, 'answer', answeredPrior.answer_text, 0, 6);
  assert.equal((await groundedIssue(premium, answerGrounding)).status, 'issued');

  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations',
    '20261121185000_deep_insight_theme_cooldown.sql'), 'utf8'));
  await db.exec('set role service_role');
  assert.equal((await state(free)).can_use_theme, true);
  assert.equal((await state(free)).theme_next_available_at, null);
  await fail('42501', () => issue(free, 'records', 'free-no-new-record'));
  assert.deepEqual((await state(free)).history, [saved.question]);
  assert.equal((await groundedIssue(free, themeGrounding, { guard: 'wrong' })).status, 'no_question');
  assert.equal((await state(free)).theme_next_available_at, null);
  const freeTheme = await groundedIssue(free, themeGrounding);
  assert.equal(freeTheme.status, 'issued');
  assert.equal((await state(free)).theme_next_available_at, freeTheme.theme_next_available_at);
  assert.deepEqual(await issue(free, 'theme', 'other-theme', { theme: '仕事・学び' }), {
    ...freeTheme, status: 'existing',
  });
  for (const [owner, hours] of [[free, 168], [plus, 24], [premium, 24]]) {
    const t = (await state(owner)).theme_next_available_at;
    const at = (date) => value('select public.deep_insight_state_at($1,$2) as v', [owner, date]);
    const earlier = new Date(Date.parse(t) - 1).toISOString();
    assert.equal((await at(earlier)).theme_available_today, false);
    const available = await at(t);
    assert.equal(available.theme_available_today, true);
    assert.equal(available.theme, null);
    const elapsed = await value(`select extract(epoch from ($2::timestamptz-issued_at))::int as v
      from public.deep_insight_questions where user_id=$1 and lane='theme' order by issued_at desc limit 1`, [owner, t]);
    assert.equal(elapsed, hours * 60 * 60);
  }
  await db.exec('reset role');
  await db.query(`update public.deep_insight_questions set issued_at=now()-interval '169 hours',
    issued_on=((now()-interval '169 hours') at time zone 'Asia/Tokyo')::date where id=$1`, [freeTheme.question.id]);
  await db.query("update public.profiles set subscription_tier='free' where id=$1", [plus]);
  await db.exec('set role service_role');
  assert.equal((await state(free)).theme_available_today, true);
  assert.ok((await state(free)).history.some((q) => q.id === freeTheme.question.id));
  assert.equal((await issue(free, 'theme', 'after-cooldown')).status, 'issued');
  const existingRecord = (await state(plus)).records;
  assert.equal((await state(plus)).can_use_records, false);
  assert.equal((await issue(plus, 'records', 'recovery')).question.id, existingRecord.id);
  assert.equal((await answer(plus, existingRecord, '切替前の問いへの回答')).inserted, true);
  await fail('42501', () => issue(plus, 'records', 'downgraded'));

  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations',
    '20261121185100_deep_insight_theme_ready_notifications.sql'), 'utf8'));
  await verifyThemeNotifications();
  await verifyThemePrivacyAndRecordsPlan(themeGrounding);
  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations',
    '20261121192000_deep_insight_record_ready_notifications.sql'), 'utf8'));
  await verifyRecordsNotifications();
  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations',
    '20261121193000_deep_insight_record_assessment_on_map.sql'), 'utf8'));
  await verifyRecordAssessmentAfterMap();
  await db.exec('reset role');
  await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations',
    '20261121194000_deep_insight_question_by_id.sql'), 'utf8'));
  await db.query(`insert into public.deep_insight_questions
    (user_id,lane,theme,question_text,issued_on,issued_at,question_key,text_key)
    select $1,'theme','人間関係','比較用の問い',current_date-n,now()-make_interval(days=>n),
      'history-before-notification-' || n,'history-before-notification-' || n
    from generate_series(2,50) as n`, [plus]);
  await db.exec('set role service_role');
  const readQuestion = (owner, id) => value('select public.deep_insight_question_by_id($1,$2) as v', [owner, id]);
  const oldQuestion = await value(`select id as v from public.deep_insight_questions
    where user_id=$1 and question_key='history-before-notification-50'`, [plus]);
  assert.ok(!(await state(plus)).history.some((q) => q.id === oldQuestion));
  assert.equal((await readQuestion(plus, oldQuestion)).id, oldQuestion);
  assert.equal((await readQuestion(plus, existingRecord.id)).answer_text, '切替前の問いへの回答');
  await fail('P0002', () => readQuestion(free, oldQuestion));
  await fail('P0002', () => readQuestion(plus, '00000000-0000-0000-0000-000000000000'));

  for (const role of ['anon', 'authenticated']) {
    await db.exec('set role ' + role);
    await fail('42501', () => state(free));
    await fail('42501', () => themeContext(free, '人間関係'));
    await fail('42501', () => readQuestion(plus, oldQuestion));
    await fail('42501', () => db.query('select * from public.deep_insight_questions'));
    await fail('42501', () => db.query('select * from public.deep_insight_theme_notification_settings'));
    await fail('42501', () => value('select public.deep_insight_theme_notification_write($1,true) as v', [free]));
    await fail('42501', () => value('select public.deep_insight_theme_notification_enqueue_due() as v'));
    await fail('42501', () => value('select public.deep_insight_theme_notification_can_send($1,$2) as v',
      [free, freeTheme.question.id]));
    await fail('42501', () => value('select public.deep_insight_record_notification_can_send($1,$2) as v',
      [free, first.id]));
    await fail('42501', () => value('select public.deep_insight_record_assessment_settle($1,$2,now(),now(),false) as v',
      ['test-job', 'test-worker']));
    await fail('42501', () => answer(free, first, saved.question.answer_text));
    await fail('42501', () => value('select public.deep_insight_issue_grounded($1,current_date,$2,$3,$4,$5,$6,$7,$8) as v',
      [free, 'records', null, 'x', 'x', 'x', 'x', JSON.stringify(grounding)]));
  }
  await db.exec('reset role');
  await db.query('delete from auth.users where id=$1', [free]);
  assert.equal(await value('select count(*)::int as v from public.deep_insight_questions where user_id=$1', [free]), 0);
  await db.close();
}

run().catch(error => { console.error(error); process.exitCode = 1; });
