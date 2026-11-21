// Load the actual source relations and the DeepInsight migration in an empty,
// isolated PostgreSQL runtime. No external data, service or model is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { PGlite } = require(process.env.Q2_PGLITE_MODULE);

const root = path.resolve(__dirname, '../..');
const db = new PGlite();
const free = '00000000-0000-0000-0000-000000000001';
const plus = '00000000-0000-0000-0000-000000000002';
const premium = '00000000-0000-0000-0000-000000000003';
const value = async (sql, args = []) => (await db.query(sql, args)).rows[0].v;
const state = (user) => value('select public.deep_insight_state($1) as v', [user]);
const context = (user) => value('select public.deep_insight_candidate_context($1) as v', [user]);
const issue = async (user, lane, key, { day, guard } = {}) => value(
  'select public.deep_insight_issue($1,$2,$3,$4,$5,$6,$7,$8) as v',
  [user, day ?? (await state(user)).day, lane, lane === 'theme' ? '人間関係' : null,
    '大切にしていることは何ですか？ ' + key, key, 'question-' + key, guard ?? (await context(user)).guard]);
const answer = (user, row, text) => value('select public.deep_insight_answer($1,$2,$3) as v', [user, row.id, text]);
const fail = (code, run) => assert.rejects(run, error => error.code === code);

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
    '20261121132000_deep_insight_questions.sql',
  ]) await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations', file), 'utf8'));

  await db.query('insert into auth.users values($1),($2),($3)', [free, plus, premium]);
  await db.query("insert into public.profiles values($1,'free'),($2,'plus'),($3,'premium')", [free, plus, premium]);
  await db.query("insert into public.emotions values(gen_random_uuid(),$1,now() at time zone 'UTC','本人の記録',null,null,null,null)", [free]);
  await db.exec('set role service_role');
  assert.equal((await state(free)).can_use_theme, false);
  assert.deepEqual((await context(plus)).material.records, []);
  assert.equal((await context(free)).material.records[0].thought, '本人の記録');
  await fail('42501', () => issue(free, 'theme', 'forbidden'));
  assert.equal((await issue(free, 'records', 'stale', { guard: 'incorrect' })).status, 'no_question');
  const first = (await issue(free, 'records', 'reflection')).question;
  assert.equal(first.lane, 'records');
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

  const theme = (await issue(plus, 'theme', 'theme')).question;
  assert.equal(theme.theme, '人間関係');
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
  assert.equal((await issue(premium, 'records', 'next-question')).status, 'issued');

  for (const role of ['anon', 'authenticated']) {
    await db.exec('set role ' + role);
    await fail('42501', () => state(free));
    await fail('42501', () => db.query('select * from public.deep_insight_questions'));
    await fail('42501', () => answer(free, first, saved.question.answer_text));
  }
  await db.exec('reset role');
  await db.query('delete from auth.users where id=$1', [free]);
  assert.equal(await value('select count(*)::int as v from public.deep_insight_questions where user_id=$1', [free]), 0);
  await db.close();
}

run().catch(error => { console.error(error); process.exitCode = 1; });
