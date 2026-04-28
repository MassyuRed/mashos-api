# ASTOR Worker Operations

対象: Cocolon 新国家システム / 高負荷・処理速度対策

この資料は、API process に重い後続処理を抱え込ませず、ASTOR worker を最大活用するための運用メモです。

## 1. 基本方針

高負荷時は、API service と worker service を分けます。

- API service: `/emotion/submit` などの即時応答、保存、enqueue
- Worker service: snapshot / analysis / ranking / summary / inspection / FCM通知送信 などの後続処理
- DB: `astor_jobs` queue と成果物保存

API service で必ず有効化する環境変数:

```env
COCOLON_HIGH_LOAD_MODE=true
ASTOR_WORKER_QUEUE_ENABLED=true
ASTOR_WORKER_QUEUE_FALLBACK_LOCAL=false
FCM_PUSH_QUEUE_ENABLED=true
FCM_PUSH_QUEUE_FALLBACK_DIRECT=false
```

`ASTOR_WORKER_QUEUE_FALLBACK_LOCAL=false` のため、worker service が起動していないと job は処理されません。高負荷モードでは worker service の常時起動が必須です。

## 2. worker service の起動

基本コマンド:

```bash
cd mashos-api/ai/services/ai_inference
python astor_worker.py
```

必須環境変数:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
ASTOR_JOBS_TABLE=astor_jobs
ASTOR_WORKER_PROFILE=all
ASTOR_WORKER_LOG_LEVEL=INFO
```

## 3. worker profile

`ASTOR_WORKER_PROFILE` で worker の担当範囲を分けられます。

| profile | 用途 |
|---|---|
| `all` | 全jobを処理する通常worker |
| `core` | myprofile / snapshot / account / feed / global summary / ranking refresh |
| `analysis` | 感情分析・自己構造分析・report生成など重い生成系 |
| `inspect` | 生成物inspection / publish gate系 |
| `ranking` | ranking refresh / inspect |
| `summary` | account / friend feed / global summary |
| `notification` | FCM push 送信専用。token解決とFirebase外部通信をAPIから切り離す |

初期運用では `all` を1本で十分です。queue滞留が出たら、profile分割してworkerを増やします。

## 4. 推奨増設順

### 小規模

```text
API service x 1
worker-all x 1
```

### 入力やHome更新が増えてきた時

```text
API service x 1
worker-core x 1
worker-analysis x 1
worker-inspect x 1
worker-notification x 1
```

### ranking / summary の更新が重くなった時

```text
API service x 1以上
worker-core x 1
worker-analysis x 1以上
worker-inspect x 1
worker-ranking x 1
worker-summary x 1
worker-notification x 1以上
```

### analysis queue が詰まる時

まず増やす対象:

```text
worker-analysis
```

analysisはCPU/DB負荷が比較的大きいため、増やしすぎるとSupabase側へ負荷が寄ります。`ready_queued` と `oldest_ready_age_seconds` を見ながら増やします。

### FCM通知queue が詰まる時

まず増やす対象:

```text
worker-notification
```

`send_fcm_push_v1` は Firebase への外部通信を含むため、API / analysis worker とは分けるのが安全です。`oldest_ready_age_seconds` が `notification` profile で伸びる場合は、notification worker を追加します。

## 5. queue状態確認

```bash
cd mashos-api
python scripts/astor_worker_status.py
```

JSONで確認:

```bash
python scripts/astor_worker_status.py --json
```

profile別に確認:

```bash
python scripts/astor_worker_status.py --profile analysis
python scripts/astor_worker_status.py --profile inspect
python scripts/astor_worker_status.py --profile notification
```

stale running job を戻す:

```bash
python scripts/astor_worker_status.py --requeue-stale --stale-running-seconds 900
```

CI / cron / health check で圧力判定する場合:

```bash
python scripts/astor_worker_status.py --fail-on-pressure --ready-threshold 50 --stale-threshold 1
```

exit code `2` の場合は worker増設またはstale job確認の対象です。

## 6. worker内の自動メンテナンス

`astor_worker.py` は定期的に次を実行します。

- queue stats log
- stale running job の再queue

環境変数:

```env
ASTOR_WORKER_MAINTENANCE_INTERVAL_SECONDS=60
ASTOR_WORKER_QUEUE_STATS_LOG_ENABLED=true
ASTOR_WORKER_STALE_RUNNING_SECONDS=900
ASTOR_WORKER_STALE_REQUEUE_LIMIT=25
```

`ASTOR_WORKER_STALE_RUNNING_SECONDS` は、1 job が正常に長く走る可能性がある場合は長めにします。短すぎると、まだ実行中のjobを再queueする危険があります。

## 7. 増設判断の目安

見る指標:

| 指標 | 意味 | 対応 |
|---|---|---|
| `ready_queued` | 今すぐ処理できる滞留job | 継続的に増えるならworker追加 |
| `delayed_queued` | debounce待ちjob | 急に増えるのは自然。ready化後を見る |
| `oldest_ready_age_seconds` | 最古ready jobの待ち時間 | 大きくなるなら処理能力不足 |
| `running` | 実行中job | worker数の目安 |
| `stale_running_count` | worker停止などで取り残された可能性 | stale requeue / worker再起動確認 |
| `failed` | 失敗job | 原因調査。単純にworker増設では解決しない場合あり |
| `send_fcm_push_v1` の ready滞留 | FCM外部通信待ち / notification worker不足 | `worker-notification` 追加、FCM credential確認 |

増やす順番:

1. `oldest_ready_age_seconds` が伸びるprofileを特定
2. `send_fcm_push_v1` が詰まる場合は `worker-notification` を1本追加
3. それ以外はそのprofileのworkerを1本追加
3. Supabase負荷と失敗率を確認
4. それでも滞留する場合にさらに追加

## 8. 専用job type worker

手動でjob typeを指定する場合:

```env
ASTOR_WORKER_JOB_TYPES=analyze_emotion_structure_standard_v1,analyze_self_structure_standard_v1
ASTOR_WORKER_INCLUDE_REQUIRED_JOB_TYPES=false
```

`ASTOR_WORKER_INCLUDE_REQUIRED_JOB_TYPES=true` のままだと、古い環境変数でも全必須jobを拾う互換動作になります。専用workerでは `false` にしてください。

## 9. 最低限の本番構成

高負荷を想定する場合の最低限:

```text
API service:
  COCOLON_HIGH_LOAD_MODE=true
  ASTOR_WORKER_QUEUE_ENABLED=true
  ASTOR_WORKER_QUEUE_FALLBACK_LOCAL=false

Worker service:
  ASTOR_WORKER_PROFILE=all
  ASTOR_WORKER_STALE_RUNNING_SECONDS=900
  ASTOR_WORKER_QUEUE_STATS_LOG_ENABLED=true
```

この構成で、APIは重処理をworkerへ逃がし、worker停止時のrunning取り残しも復旧しやすくなります。


## 10. FCM通知専用queue

感情入力通知やレポート配布通知は、API / cron が直接 Firebase へ送らず、`astor_jobs` に `send_fcm_push_v1` としてenqueueします。

```text
API / cron
  ↓
send_fcm_push_v1 job
  ↓
worker-notification
  ↓
push_token 解決
  ↓
FCM送信
```

API service側の推奨値:

```env
FCM_PUSH_QUEUE_ENABLED=true
FCM_PUSH_QUEUE_FALLBACK_DIRECT=false
```

notification worker側の推奨値:

```env
ASTOR_WORKER_PROFILE=notification
FCM_PUSH_ENABLED=true
FCM_SERVICE_ACCOUNT_FILE=/etc/secrets/firebase_service_account.json
```

`FCM_PUSH_QUEUE_FALLBACK_DIRECT=false` にすると、queue enqueue に失敗した場合もAPI側では直接FCM外部通信を行いません。高負荷時はこの設定を維持し、notification worker と queue監視で回収します。

## 11. 負荷試験との接続

worker増設判断は、API latency と queue status を同時に見て行います。

基本手順:

```bash
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 100 --concurrency 20 --no-notify-friends
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 100 --concurrency 20 --notify-friends
python scripts/astor_worker_status.py --profile notification
python scripts/astor_worker_status.py --profile analysis
python scripts/astor_worker_status.py --profile core
```

詳細は `ai/docs/LOAD_TESTING.md` を参照してください。

判断の軸:

- APIの `p95 / p99` が高い場合は、まず該当endpointの処理内容を見る
- `ready_queued` が増え続ける場合は、該当profileのworkerを増やす
- `send_fcm_push_v1` だけが詰まる場合は `worker-notification` を増やす
- `failed` が増える場合は worker数ではなく処理失敗原因を見る
