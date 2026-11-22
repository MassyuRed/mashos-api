// Disposable PostgreSQL WASM: real Piece foundation/access/receipt migrations.
const { PGlite } = require(process.env.Q2_PGLITE_MODULE);
const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');
(async () => {
  const db = new PGlite();
  await db.exec(`CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;
    CREATE VIEW public.mymodel_reflections_read WITH (security_invoker=true) AS SELECT 1 AS fixture;`);
  for (const file of ['20260808_002_piece_v2_foundation.sql', '20260808_003_piece_v2_rls_and_staging.sql',
    '20261104002458_piece_v2_export_receipt.sql']) {
    await db.exec(fs.readFileSync(path.resolve(__dirname, '../../../supabase/migrations', file), 'utf8'));
  }
  process.stdout.write(JSON.stringify({ready:true})+'\n');
  for await (const line of readline.createInterface({input:process.stdin})) {
    const q=JSON.parse(line);
    try {
      if (q.role) {
        if (!['anon','authenticated','service_role'].includes(q.role)) throw Error('Invalid test role');
        await db.exec(`SET ROLE ${q.role}`);
      }
      const result=await db.query(q.sql,q.params);
      process.stdout.write(JSON.stringify({rows:result.rows})+'\n');
    } catch(e) { process.stdout.write(JSON.stringify({code:e.code,message:e.message})+'\n'); }
    finally { await db.exec('RESET ROLE'); }
  }
  await db.close();
})().catch(e=>{ process.stderr.write(String(e)); process.exit(1); });
