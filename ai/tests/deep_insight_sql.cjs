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
const issue = async (user, lane, key, { day, guard } = {}) => value(
  'select public.deep_insight_issue($1,$2,$3,$4,$5,$6,$7,$8) as v',
  [user, day ?? (await state(user)).day, lane, lane === 'theme' ? '人間関係' : null,
    '大切にしていることは何ですか？ ' + key, key, 'question-' + key, guard ?? (await context(user)).guard]);
const answer = (user, row, text) => value('select public.deep_insight_answer($1,$2,$3) as v', [user, row.id, text]);
const fail = (code, run) => assert.rejects(run, error => error.code === code);

const groundedIssue = async (user, receipt, { day, guard } = {}) => value(
  'select public.deep_insight_issue_grounded($1,$2,$3,$4,$5,$6,$7,$8,$9) as v',
  [user, day ?? (await state(user)).day, receipt.lane, receipt.lane === 'theme' ? '人間関係' : null,
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
    '20261114120000_analysis_if_route_artifacts.sql',
    '20261114123000_analysis_emlis_material_handoff.sql',
    '20261114132000_analysis_map_interpretation_corrections.sql',
    '20261114133000_analysis_map_correction_handoff.sql',
    '20261121132000_deep_insight_questions.sql',
    '20261121133000_analysis_deep_insight_answer_handoff.sql',
    '20261121134000_deep_insight_grounded_questions.sql',
  ]) await db.exec(fs.readFileSync(path.join(root, 'supabase/migrations', file), 'utf8'));

  await db.query('insert into auth.users values($1),($2),($3)', [free, plus, premium]);
  await db.query("insert into public.profiles values($1,'free'),($2,'plus'),($3,'premium')", [free, plus, premium]);
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
      round_index: 1, original_source_ref: 'original', answer_text_private: '本人が答えた材料' } })]);
  original = (await context(free)).material.records[0];
  const emlisAnswer = original.emlis_answered_questions[0];
  assert.equal(emlisAnswer.id, answerEventId);
  assert.equal(emlisAnswer.question_id, 'emlis-question');
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

  for (const role of ['anon', 'authenticated']) {
    await db.exec('set role ' + role);
    await fail('42501', () => state(free));
    await fail('42501', () => db.query('select * from public.deep_insight_questions'));
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
