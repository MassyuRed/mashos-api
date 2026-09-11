// Test-only PostgreSQL WASM bridge. Q2_PGLITE_MODULE points to PGlite 0.5.8.
const { PGlite } = require(process.env.Q2_PGLITE_MODULE);
const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');
(async () => {
  const db = new PGlite();
  await db.exec(`create schema auth;
    create role anon; create role authenticated; create role service_role bypassrls;
    create table auth.users(id uuid primary key);
    create table public.profiles(id uuid primary key references auth.users on delete cascade, subscription_tier text);
    create table public.emotions(id uuid primary key, user_id uuid references auth.users on delete cascade,
      created_at timestamp, memo text, memo_action text, category text[], emotions text[], emotion_details jsonb);
    grant usage on schema public,auth to service_role;
    grant select on auth.users,public.profiles,public.emotions to service_role;
    grant update on public.profiles,public.emotions to service_role;`);
  await db.exec(fs.readFileSync(path.resolve(__dirname, '../../../supabase/migrations/20260911020509_emlis_input_threads_q2.sql'), 'utf8'));
  process.stdout.write(JSON.stringify({ready:true})+'\n');
  for await (const line of readline.createInterface({input:process.stdin})) {
    const q=JSON.parse(line);
    try {
      if (q.role) await db.exec(`set role ${['anon','authenticated','service_role'].includes(q.role)?q.role:'postgres'}`);
      const result=await db.query(q.sql,q.params || []);
      process.stdout.write(JSON.stringify({rows:result.rows})+'\n');
    } catch(e) { process.stdout.write(JSON.stringify({code:e.code || 'test_bridge_error'})+'\n'); }
    finally { await db.exec('reset role'); }
  }
  await db.close();
})().catch(e=>{ process.stderr.write(String(e)); process.exit(1); });
