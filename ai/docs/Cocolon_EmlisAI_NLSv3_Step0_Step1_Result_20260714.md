# Cocolon EmlisAI Natural Language Surface v3 Step 0 / Step 1 実装結果

作成日: 2026-07-14

## 1. 結論

- Step 0 `revised design / version boundary freeze`: **COMPLETED**
- Step 1 `baseline / actual input contract freeze`: **COMPLETED**
- 次に許可されるのは **Step 2の開始のみ**
- NLS v3のproduction source、runtime接続、owner切替、Step 2以降は未実装
- v1 production ownerは変更せず、停止済みv2は修正・import・再開していない

Step 0のSTOP条件とStep 1のSTOP条件は発生しなかった。

## 2. 実装範囲

### Step 0

- 改訂設計書のSHA-256を固定
- NLS v3のidentity、runtime state enum、observation stage enumを固定
- 停止済みv2のsource / fixture / receiptの41ファイルをimmutable manifestとして固定
- public API / DB / RN / naming / Safetyを変更しない境界を固定
- 100件ずつ最低10巡、秘密入力不要、local安定後に実機へ進む方針を固定

Step 0 receiptはbody-freeであり、Step 1にだけ進める。runtime switchの権限は持たない。

### Step 1

- 現行v1 owner 5ファイルと、`emlis_ai_reply_service.py`からの再帰的依存closure 17ファイルをhashで固定
- 使用可能な既知28ケースで、現行v1のoutput / Gate / public visibility / latencyを実測
- RN実sourceからemotion、strength、category、自己理解排他、submit conditionを固定
- backendの後方互換容認と、現行UIから到達可能な入力contractを分離
- Known regression inventoryを11項目で固定
- 実sourceのNucleus / Relation / Unknown / Safety / Reception Opportunityから、切り捨てないrequest-relative resource boundを固定
- Supabase corpusは`not_received_not_blocking`とし、受領後のprivacy / validation / current-validとlegacyの分離手順のみを固定

既知28ケースは現行v1比較用であり、華恋作成v3最低1000件には数えない。NLS v3の実行結果としても扱わない。

## 3. 固定した事実

### Source / version boundary

- 改訂設計書 SHA-256: `6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc`
- backend受領ZIP SHA-256: `f97df95b5f7065854826051636d7d8223db49f7b1fce958697c4ae20f6a42415`
- RN受領ZIP SHA-256: `2287550897799bee5ce1ac8a4235f4aa364ed7ef088c1bd3ef7d84fd2d009100`
- v1 owner snapshot SHA-256: `ed9d7463778909c97115096345d25d6ce260d21ed737a72d7c06ccd8e08687ac`
- v1 dependency closure SHA-256: `3d42e942239666dc37d14c9c2969d548988c02e38ac497bb65b825d9b4c1f3bd`
- v2の状態: `offline_only_stopped`
- NLS v3の状態: `offline`、runtime未接続、ownerではない
- production owner: `grounded_sentence_surface_canonical_v1`

### RN app-reachable input contract

- text: trim後の`memo`または`memoAction`のどちらかが非空
- emotion: 1件以上、`喜び / 悲しみ / 怒り / 不安 / 平穏 / 自己理解`
- strength: `weak / medium / strong`
- `自己理解`は単独選択で、strengthは`medium`
- category: 1件以上、`生活 / 仕事 / 趣味 / 人間関係 / 恋愛 / 健康 / 学習 / 価値観 / 人生`
- submit condition: `not_submitting_and_text_and_emotion_and_category`

backendはlegacy string emotion、未知emotion、不正strengthの`medium`補正、自己理解と他emotionの混在、categoryなしmemo等を後方互換上受理し得る。このbackend容認はapp-valid入力のauthorityにしない。

### Source resource bound

- 現行RN / APIには`memo` / `memo_action`の固定文字数上限がないため、Nucleus / Relationの偽のglobal固定上限は追加しない
- source component上限: `N <= E`、`R <= min(N * (N - 1), T + 9)`、`U <= 11`（app-reachableは7）、`S <= 1`、Safety required boundary code `K <= 9`、`O <= 4`
- base nonstance容量を`B = 4*N + R + U`とする
- Safety default / codeごと・base targetごとのcounterposition容量を`C = (S + K) * B`とする
- Reception Opportunityが0件でもdefault reception authorityを1件分持ち、保守的な受容容量を`Q = (O + 1) * (B + C)`とする。`C`は上限を過小にしないためのcapacity余剰で、runtimeのreception targetとしては許可しない
- inventory全体の保守上限は`(4*N + R + U) * (S + K + 1) * (O + 2)`
- 同一canonical identityのsemantic duplicateは禁止し、配列authorityはlossless union、scalar conflictはplanner failureとする
- candidate上限12はinventory上限に流用しない。上限超過はtruncateせず`OBLIGATION_INVENTORY_OVERFLOW`
- `bound - 1 / bound / bound + 1`を独立テストで固定

この式は将来のStep 4実装へ渡すversion policyであり、Step 1でNLS v3 runtimeやledger本体を実装したものではない。

### v1 baseline

- cohort: exact8 = 8件、RR8 unseen12 = 12件、I6 probe8 = 8件、計28件
- 全28件で凍結したv1 output、Gate、public visibilityと再生成結果が一致
- latency: 1ケースあたりwarmup 1回 + 計測5回、計140 samples
- 計測範囲: local process内の`render_emlis_ai_reply`、HTTP / DB / networkなし
- min `2.136578 ms`、median `3.612947 ms`、p95 `6.742766 ms`、max `9.457688 ms`
- 性能acceptance budgetは発明せず、Step 15 protocolまで未確定

body-fullの既知入力とv1可視文は`tests/local_only`に分離した。shareable receiptはdomain-separated HMAC-SHA-256 commitment、case別の構造値、集計値のみで、raw input、comment text、candidate body、commitment keyを含まない。

### Known actual-device boundaries

- 2026-07-13のhistorical代表4件はcanonical v1表示との目視一致4 / 4だが、商品判定はPASS 0 / FAIL 4
- 上記は正式なv2実機評価ではなく、v2 runtime生成は0。画像レビューはraw backend bodyの暗号学的hash proofではない
- 現行UI contractから到達不能なlegacy入力を含むため、v3最低1000件にもv3進行にも数えない
- 後続R8 / RR10の代表順`A / B / I6-L03 / I6-D02`は別packetであり、actual deviceは全件`not_run`、progression authorityは`none`
- historical 4件とRR10は、receipt / raw-input owner / result doc / readiness / expected packet / evidence template / verifierの各hashで別々に固定

## 4. 成果物

| ファイル | 役割 | SHA-256 |
|---|---|---|
| `ai/tests/fixtures/emlis_nls_v3_s0_boundary_20260714.json` | Step 0 body-free receipt | `57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024` |
| `ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json` | RN / backend入力境界とresource policy | `d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6` |
| `ai/tests/local_only/emlis_nls_v3_s1_v1_visible_20260714.json` | body-full既知28ケースとv1可視baseline | `ba7e1f3d11bd7cd156da80dc6594e889b10e57b123df2e6b9c80e4345f47286d` |
| `ai/tests/fixtures/emlis_nls_v3_s1_baseline_receipt_20260714.json` | Step 1 body-free receipt | `669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518` |
| `ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py` | receipt生成・strict validation | `7f6ad6c042c0a96fb1e654bd00002256bbbca4fc0a7bd29c35866afa279b3560` |
| `ai/tests/test_emlis_nls_v3_s0_s1.py` | positive / independent negative / drift / privacyテスト | `9d76f022f308810747da7f4493ed49afe6701a02fc73255dbbedc44ace088bb4` |

上表6ファイルと本結果文書の計7ファイルが今回の新規ファイルである。既存ファイルの修正はない。

## 5. 検証結果

- 新規v3 Step 0 / Step 1 tests: **11 / 11 PASS**
- 既存v2 Step 0 / Step 1 regression tests: **8 / 8 PASS**
- historical device4 regression tests: **6 / 6 PASS**
- 直接実行したtest合計: **25 / 25 PASS**
- Python構文コンパイル: **503 / 503 PASS**
- 既存backend source 1,792ファイル: **変更0 / 欠落0**
- RN source 217ファイル: **変更0 / 欠落0**
- `pytest` CLI: environmentにpackageがないため未使用。引数なしtest 25件をPythonから直接実行し、全件PASS

## 6. 未確定・未実施

- Supabase corpusの実データ件数・内容は未確認
- NLS v3の出力品質・Gate・性能は未実測（v3 core未実装のため）
- shadow、tester-only actual device、owner switch、releaseは未実施
- R8 / RR10 actual-device baselineは`not_run`

上記を完了したことにはしない。実機作業は設計通りlocal安定後まで進めない。
