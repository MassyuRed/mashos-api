# Cocolon EmlisAI Natural Language Surface v2
## Step 0 / Step 1 実装結果

- 実装日: 2026-07-13
- 対象設計: `Cocolon_EmlisAI_ModelFreeNaturalLanguageSurfaceV2_DetailedDesign_ImplementationOrder_20260713.md`
- 実装範囲: `Step 0. 設計freeze` / `Step 1. v1 baseline receipt固定`
- 現在の商品判定: `REPAIR_REQUIRED`
- runtime owner: `v1`
- v2 runtime接続: 未実施
- Holdout A / B: 未作成・未開封
- 進行権限: `none`

---

## 1. 結論

Step 0とStep 1を実装した。

今回の作業はv2自然文生成本体の実装ではない。後続v2が現行v1より本当に改善したかを比較できるように、次を固定する工程である。

1. 設計、受領zip、現行owner、変更禁止contract、評価物の役割、Holdout開封時点をbody-free freezeへ固定した。
2. exact8、既存unseen12、既存I6 blind corpusからexact8採用分を除いたprobe8、合計28件の現行v1出力を再生成した。
3. ユーザー入力と可視本文をlocal-only artifactへ置き、body-free receiptにはhashと計測値だけを置いた。
4. 可視本文、section hash、文数、引用依存、reception predicate family、local runtime latency、public contract snapshotを固定した。
5. production code、RN、DB、route、response key、subscription、accountは変更していない。

Step 0 / Step 1の完了によってv2 runtime接続や商品PASSを許可していない。次工程は設計書のStep 2であり、今回そこへは進めていない。

---

## 2. 確認済み事実

### 2.1 受領sourceと設計basis

| 対象 | 今回受領 | SHA-256 | 設計書basis | 判定 |
|---|---|---|---|---|
| 前提資料 | `Cocolon_前提資料(334).zip` | `0fc80fb9b7bcf34fe8eb6cca8c34b19a43461c88bb64a53ca8a8de7cb03e16b9` | `(333)` | bytes一致 |
| RN | `Cocolon(297).zip` | `625a58d773d5ed8ac7da3e28d032f7467533f8bb1e3a011e457883a267f3a21e` | `(296)` | bytes一致 |
| backend | `mashos-api(222).zip` | `a5efd0e7cd110c9bb95ba543d1c68c1094951b7de160ef9cf91341eb41b5bae1` | `(221)` | bytes一致 |

番号は進んでいるが、設計書が確認した各basisとSHA-256が同じである。したがって、Step 0停止条件の「sourceが異なり、差分を確認できない」には該当しない。

設計書本体の受領SHA-256は次である。

```text
b2441917ee80b22c84973c4205bc1cb1a9c471037fe270391438cbd7d7694752
```

### 2.2 現行production owner

現行5 ownerのcanonical snapshot SHA-256は次である。

```text
ed9d7463778909c97115096345d25d6ce260d21ed737a72d7c06ccd8e08687ac
```

対象:

- `emlis_ai_grounded_observation_plan.py`
- `emlis_ai_grounded_human_reception.py`
- `emlis_ai_grounded_sentence_surface.py`
- `emlis_ai_grounded_observation_gate.py`
- `emlis_ai_reply_service.py`

production replyは引き続き次を使用する。

```text
generation_method = functional_atom_grounded_realizer
composer_source = grounded_plan_realizer
generation_path = grounded_observation_plan_sentence_surface_canonical_v1
```

### 2.3 評価物の位置づけ

| 評価物 | Step 0で固定した役割 |
|---|---|
| exact8 | 入力identity、意味・安全・二段表示回帰、v1比較baseline。v2正解文ではない。Holdoutではない。 |
| existing unseen12 | 既に本文を見ているdevelopment / regression。Holdoutではない。 |
| existing I6 probe8 | 既存I6 blind corpusのうちexact8採用4件を除いた追加probe。新規入力を発明していない。 |
| 最新実機画像 | 設計書が記録した商品問題の根拠。今回再添付されていないため、runtime hash証拠としては扱わない。 |

### 2.4 変更禁止contract

次を変更していない。

- `/emotion/submit`
- `input_feedback.comment_text`
- `input_feedback.emlis_ai.observation_status`
- `passed + non-empty comment_text`のRN表示条件
- `見えたこと → Emlisから`の二段順序
- DB physical name / write path
- legacy façade / bridge
- account / subscription / entitlement
- user data protection
- grounding / safety / body-free meta
- deterministic runtime

---

## 3. Step 0 実装

追加したfreeze:

```text
ai/tests/fixtures/emlis_nls_v2_s0_freeze_20260713.json
```

固定内容:

- 全受領物のSHA-256
- 設計書basisと今回受領zipのbytes一致
- 現行source ownerとsource snapshot
- `REPAIR_REQUIRED`
- 実装対象 / 非対象
- exact8 / unseen12 / 最新実機画像の役割
- 外部APIなし / ローカルLLMなし
- 変更禁止contract
- RN public contract owner hash
- Holdout A / Bの未作成・未開封
- Holdout Aはv2 freeze後のStep 8で初回開封
- Holdout Bはコード無変更のStep 9で初回開封
- v1 production owner維持
- v2 runtime未接続

freeze SHA-256:

```text
7a6b02e2abfa1b60cea681238a1482f4b310f0010214e7fd8e7175bd891fdddd
```

---

## 4. Step 1 実装

### 4.1 cohort

| cohort | 件数 | 役割 |
|---|---:|---|
| exact8 | 8 | canonical app-valid regression / v1比較 |
| existing unseen12 | 12 | 既存development / regression |
| existing I6 probe8 | 8 | 既存blind corpusの残り |
| 合計 | 28 | v1 baseline |

### 4.2 body-full / body-free分離

body-full local-only artifact:

```text
ai/tests/local_only/emlis_nls_v2_s1_visible_20260713.json
```

内容:

- current input
- current input SHA-256
- v1 visible surface
- full visible SHA-256
- `見えたこと`本文 / section SHA-256
- `Emlisから`本文 / section SHA-256
- public status
- v1 generation owner

SHA-256:

```text
3d7cbb5487901027c83a9082bd10d872b87412cd50a6d94a14f6585c9cad199e
```

body-free receipt:

```text
ai/tests/fixtures/emlis_nls_v2_s1_receipt_20260713.json
```

内容:

- source / fixture / visible artifact hash
- case identityと各section hash
- 文数
- quote dependency
- reception predicate family
- local runtime latency
- public contract snapshot
- v1比較baselineでありv2 expected textではないこと
- Holdout未開封、progression authorityなし

receipt SHA-256:

```text
fff9164a291907b2dea03f2e062bc3db808d2728db6b9217f0e823d977721af7
```

### 4.3 v1計測値

計測範囲は、local process内の`render_emlis_ai_reply`である。HTTP route、DB、networkは含まない。各case 1 warmup後に5回、合計140 sampleを取得した。

| 指標 | 結果 |
|---|---:|
| latency min | 1.951778 ms |
| latency median | 3.623868 ms |
| latency p95 | 6.958008 ms |
| latency max | 9.312831 ms |

これは今回環境の比較baselineであり、runtime接続時の受入予算ではない。絶対性能予算は設計どおりStep 10 shadow前に固定する。

文数分布:

| section | 分布 |
|---|---|
| 見えたこと | 1文: 8 / 2文: 7 / 3文: 9 / 4文: 3 / 5文: 1 |
| Emlisから | 1文: 12 / 2文: 16 |
| 可視本文全体 | 2文: 8 / 3文: 3 / 4文: 5 / 5文: 8 / 6文: 3 / 7文: 1 |

quote dependencyは、各section内の`「...」` / `『...』`内文字数をsection非空白文字数で割ったbasis pointsである。

| section | median | max |
|---|---:|---:|
| 見えたこと | 4232 | 6992 |
| Emlisから | 0 | 2727 |

reception predicate family分布:

| family | count |
|---|---:|
| `human_response_attention_stood_out` | 12 |
| `human_response_quiet_presence` | 12 |
| `human_response_recognize_change` | 6 |
| `human_response_bounded_counterposition` | 5 |
| `human_response_felt_respect_for_effort` | 4 |
| `human_response_hold_help_seeking` | 3 |
| `human_response_felt_gentle_respect` | 1 |
| `human_response_significance_intention_preserved` | 1 |

一つのcaseが複数predicate familyを持つため、合計は28を超える。

predicate / terminal / skeletonの正式な集中上限は、Step 2のDevelopment 42件baseline前には固定しない。今回の28件を70件cohortの代用にして上限を発明していない。

---

## 5. 再生成helper / contract test

追加helper:

```text
ai/tests/helpers/emlis_nls_v2_s1_baseline.py
```

役割:

- exact8 input identityの検証
- existing unseen12とexisting I6 probe8の読込
- 現行v1の再生成
- local-only visible artifact生成
- body-free receipt生成
- 5 owner source hash検証
- public contract検証
- 同一入力・同一sourceでのvisible hash決定性検証
- latency / sentence / quote / predicate計測

再生成コマンド:

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference:tests \
python tests/helpers/emlis_nls_v2_s1_baseline.py \
  --write --warmup-runs 1 --latency-samples 5
```

追加test:

```text
ai/tests/test_emlis_nls_v2_s0_s1.py
```

検査内容:

- design / source / RN freeze
- exact8 / unseen12 / probe8 identity
- 28件のlive v1再生成とfull / section hash一致
- body-full / body-free分離
- raw input / visible bodyのreceipt非混入
- sentence / quote / predicate metrics再計算一致
- public status / comment表示契約
- v1 production owner維持
- v2 runtime module未作成
- Holdout未開封

---

## 6. 検証結果

### backend Step 0 / 1 contract

環境に`pytest` packageが存在しなかったため、`pytest` CLIは実行できなかった。packageを外部取得して環境を変えず、新規test module内の8 test関数を同じPython processで直接実行した。

```text
8 passed
```

28件すべてで、現行sourceから次が再生成一致した。

- visible surface
- visible surface SHA-256
- observation section / SHA-256
- reception section / SHA-256
- public `passed`
- final runtime contract guard `passed`
- sentence count
- quote dependency
- predicate family

exact8 8件のfull / section hashは、既存RR9 visible packetのexact8と全件一致した。

### Python compile

新規helper / testの`compileall`はPASSした。

### RN public contract

受領した`Cocolon(297).zip`で次を実行した。

```text
node --test tests/rn-screen-contracts.test.js
```

結果:

```text
36 passed / 0 failed
```

### 未実行

- pytestによるbackend既存suite全体
- HTTP / DB / networkを含む実runtime latency
- 実機表示
- Holdout A / B
- v2商品読感

これらをStep 0 / Step 1のPASSへ含めていない。

---

## 7. 推測

- なし。zip番号差はSHA-256一致で確認し、内容差がないと判定した。
- latencyは今回local processの実測であり、production latencyへ外挿していない。
- 最新実機画像は今回の受領物にないため、設計書が記録した役割だけをfreezeし、画像を再確認したとは扱っていない。

---

## 8. 華恋の意見

Step 0 / Step 1で重要なのは、現行文を「正解」として固めることではなく、v2が改善したと言える比較点を失わないことである。

今回のbaselineでは、`見えたこと`のquote dependency中央値が42.32%、最大69.92%であり、`Emlisから`のpredicate familyも`attention_stood_out`と`quiet_presence`へ各12回集まっている。これは設計書が指摘した「見えたことの引用近接」と「Emlisからの反応範囲集中」を、完成文の感想だけではなく比較可能な数値へ固定できたという意味を持つ。

一方、この28件だけでv2の集中上限を決めるのは早い。14 family × Development 3件の42件を固定するStep 2の前に閾値を置くと、現行case構成へ合わせた上限になる。そのため、今回は分布を保存し、正式上限は未固定のまま止めた。

---

## 9. 現在の固定状態

```text
step0_status = completed
step1_status = completed
current_product_status = REPAIR_REQUIRED
runtime_owner = v1
v2_runtime_connected = false
holdout_a_created = false
holdout_a_opened = false
holdout_b_created = false
holdout_b_opened = false
external_api_used = false
local_llm_used = false
production_code_changed = false
rn_code_changed = false
db_changed = false
progression_authority = none
```

次に実行すべき設計上の工程はStep 2である。今回の指示範囲には含まれないため、実装していない。
