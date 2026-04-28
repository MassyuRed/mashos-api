# Cocolon load testing guide

この資料は、新国家システムの高負荷・速度対策を実測するための最小手順です。

重要な前提として、100人 / 1000人規模に耐えられるかは、実ファイルの構造確認だけでは断定できません。API応答時間、queue滞留、worker処理時間、Supabase側の上限を実測して判断します。

## 1. 使うscript

```bash
python scripts/cocolon_load_test.py --help
```

主な対象endpoint:

| scenario | endpoint | 用途 |
|---|---|---|
| `app-bootstrap` | `GET /app/bootstrap` | 起動時の軽量状態確認 |
| `startup` | `GET /app/startup` | startup bundle確認 |
| `home-state` | `GET /home/state` | Home read確認 |
| `emotion-submit` | `POST /emotion/submit` | 感情入力hot path確認 |
| `piece-preview` | `POST /emotion/piece/preview` | Piece preview確認 |
| `custom-get` | 任意GET | 補助測定 |
| `custom-post` | 任意POST | 補助測定 |
| `mix` | startup/read/write混合 | read-heavy + 少量write確認 |

## 2. 最初のread負荷確認

```bash
export COCOLON_LOAD_BEARER_TOKEN="<staging user jwt>"

python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario app-bootstrap \
  --requests 100 \
  --concurrency 20
```

次に startup / home を確認します。

```bash
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario startup --requests 100 --concurrency 20
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario home-state --requests 100 --concurrency 20
```

見る指標:

```text
success_rate
status_counts
latency_ms.p50
latency_ms.p95
latency_ms.p99
requests_per_second
```

## 3. 感情入力hot path確認

通常の保存速度を確認する場合は、通知を切ります。

```bash
python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario emotion-submit \
  --requests 50 \
  --concurrency 10 \
  --no-notify-friends
```

段階的に増やします。

```bash
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 100 --concurrency 10 --no-notify-friends
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 300 --concurrency 30 --no-notify-friends
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 500 --concurrency 50 --no-notify-friends
```

## 4. FCM queue経路確認

通知queueを含めて確認する場合だけ、`--notify-friends` を使います。

```bash
python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario emotion-submit \
  --requests 100 \
  --concurrency 20 \
  --notify-friends
```

この時、APIのp95/p99だけでなく notification queue を確認します。

```bash
python scripts/astor_worker_status.py --profile notification
```

確認する値:

```text
ready_queued
oldest_ready_age_seconds
running
failed
stale_running_count
send_fcm_push_v1 の queued/running/failed
```

`ready_queued` と `oldest_ready_age_seconds` が増え続ける場合は、`worker-notification` を追加します。

## 5. Piece preview確認

Piece previewは生成と保存を含むため、最初は小さく確認します。

```bash
python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario piece-preview \
  --requests 30 \
  --concurrency 5 \
  --no-notify-friends
```

増やす場合:

```bash
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario piece-preview --requests 100 --concurrency 10 --no-notify-friends
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario piece-preview --requests 200 --concurrency 20 --no-notify-friends
```

## 6. 複数ユーザーtokenでの確認

`tokens.txt` に1行1tokenで入れます。

```text
<jwt-user-1>
<jwt-user-2>
<jwt-user-3>
```

実行:

```bash
python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario mix \
  --token-file tokens.txt \
  --requests 300 \
  --concurrency 30
```

## 7. duration mode

固定request数ではなく、一定時間流します。

```bash
python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario startup \
  --duration-seconds 60 \
  --concurrency 50
```

## 8. JSON出力

```bash
python scripts/cocolon_load_test.py \
  --base-url "https://<api-host>" \
  --scenario emotion-submit \
  --requests 100 \
  --concurrency 20 \
  --no-notify-friends \
  --output-json load-result.json
```

## 9. 目安

最初の確認では、絶対値よりも次を見ます。

| 指標 | 見方 |
|---|---|
| p50 | 普段の体感速度 |
| p95 | 混雑時の体感速度 |
| p99 | 尖った遅延・詰まり |
| 5xx | backend側の処理崩れ |
| 401/403 | token / auth設定ミス |
| 429 | rate limit / Supabase / gateway圧 |
| queue ready滞留 | worker不足 |
| oldest_ready_age_seconds | worker増設判断 |
| failed job | 処理失敗原因の調査対象 |

## 10. 実行時の注意

- まず staging で実行します。
- `emotion-submit` と `piece-preview` は実データを作るため、テストユーザーで実行します。
- 通知経路の確認時以外は `--no-notify-friends` を使います。
- FCM queue確認時は `worker-notification` を起動しておきます。
- 負荷試験中は、別terminalでqueue statusを確認します。

```bash
watch -n 5 'python scripts/astor_worker_status.py --profile notification'
watch -n 5 'python scripts/astor_worker_status.py --profile analysis'
watch -n 5 'python scripts/astor_worker_status.py --profile core'
```

## 11. 判断フロー

```text
API p95/p99 が高い
  ↓
read endpoint だけ高い？
  → cache / snapshot / Supabase readを確認
write endpoint だけ高い？
  → /emotion/submit の保存・EmlisAI timeout・Supabase writeを確認
queue readyが増え続ける？
  → 該当profile workerを追加
failed jobが増える？
  → worker数ではなく処理失敗原因を調査
notificationだけ詰まる？
  → worker-notification追加 / FCM credential / FCM外部通信を確認
```

## 12. 本番前の最低確認セット

```bash
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario app-bootstrap --requests 100 --concurrency 20
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario startup --requests 100 --concurrency 20
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario home-state --requests 100 --concurrency 20
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 100 --concurrency 20 --no-notify-friends
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario emotion-submit --requests 100 --concurrency 20 --notify-friends
python scripts/cocolon_load_test.py --base-url "https://<api-host>" --scenario piece-preview --requests 50 --concurrency 10 --no-notify-friends
python scripts/astor_worker_status.py --profile notification
python scripts/astor_worker_status.py --profile analysis
python scripts/astor_worker_status.py --profile core
```
