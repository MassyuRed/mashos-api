# Cocolon EmlisAI Natural Language Surface v3 — Step 2 実装結果

- 実施日: 2026-07-14
- 対象: `Step 2. sample schema / App-Reachable Validator / corpus registry`
- 結果: **completed**
- runtime 接続: **未実施**
- batch 001 本文: **未作成**
- EmlisAI 実行: **未実施**

## 1. 親・入力の固定

| 対象 | SHA-256 |
|---|---|
| 受領 ZIP `mashos-api_2(149).zip` | `87dccb6b87be2aca7a56ab93ad77dbcea90c87d96e834317eb005fbaa1f0926a` |
| revised design | `6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc` |
| Step 0 boundary | `57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024` |
| Step 1 input contract | `d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6` |
| Step 1 visible local-only artifact | `ba7e1f3d11bd7cd156da80dc6594e889b10e57b123df2e6b9c80e4345f47286d` |
| Step 1 baseline receipt | `669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518` |
| Step 0/1 helper | `7f6ad6c042c0a96fb1e654bd00002256bbbca4fc0a7bd29c35866afa279b3560` |
| Step 0/1 test | `9d76f022f308810747da7f4493ed49afe6701a02fc73255dbbedc44ace088bb4` |

受領 ZIP は `unzip -t` で完全性を確認した。Step 0/1 の上記6成果物は受領時からbyte不変である。

## 2. 実装した境界

### 2.1 `sample_case.v1`

- Draft 2020-12 JSON Schemaを実ファイル化した。
- top-level、input、emotion、semantic contract、coverageをclosed objectにした。
- emotionは`oneOf`で次の2形だけを許可する。
  - 自己理解以外の1〜5件
  - `自己理解 / medium`の単独1件
- categoryは現行RNの9種類、1件以上、重複なしに固定した。
- thought/actionには設計に存在しない文字数上限を追加していない。
- expected final text、generation hint等のschema外annotationを拒否する。

### 2.2 App-Reachable Validator

- Step 1で固定したRN input contractをauthorityにした。
- JavaScript `String.trim()`と同じECMAScript whitespace集合を明示実装した。
- Python `str.strip()`との差が出る`U+FEFF`、`U+0085`、`U+001C`、`U+200B`を独立試験した。
- emotion/categoryのunknown、空、非array、重複を拒否する。
- `自己理解 + 他感情`と`自己理解 / medium以外`を独立REDで拒否する。
- backendの許容範囲をApp-Reachableのauthorityへ昇格させていない。
- validator / duplicate policyはcanonical hashで固定し、process内でdictが書き換わった場合もvalidator・checker・registry builderをfail-closedにする。
- nested emotionのtype/strengthがarray/object等でも例外へ崩れず、型issueとして拒否する。

### 2.3 exact / normalized / near duplicate

- exact input identityと、annotationを含むfull case commitmentを分離した。
- normalized identityはNFKC、ECMAScript trim/whitespace collapse、RN option順を使用する。
- nearは双方向`SequenceMatcher`とcharacter bigram Diceの対称な最大値を使用する。
- sample順を反転しても同じreportになる。
- nearはsilent mergeせずreview candidateとし、`accepted_distinct`または`reject_duplicate`の明示判断を要求する。
- 計算budgetを超えた場合は入力をinvalidにせず、novelty checkをindeterminateとしてfreezeを拒否する。
- Karen review済みother-AI syntheticもvalidator / novelty / coverageへ通せるが、Karen 100件manifestへは混在させず、最低件数へ算入しない。

### 2.4 coverage matrix / batch manifest

- revised designの14 family、全直交coverage軸、4 structural variation flagを保持する。
- matrixはsampleから全件再集計し、本文を持たない。
- schemaのaxis/valueもclosed enumにし、body-free fieldへの任意本文注入を許可しない。
- batch manifestはactual corpus、coverage matrix、duplicate report、parent registryの実bytes/hashへbindする。
- artifact refはrepo-root基準の安全なrelative pathだけを許可する。
- Step 2 manifest stateは設計の`DRAFT` / `VALIDATED`を使用し、immutable lockは別の`frozen` booleanで表す。
- `VALIDATED`はKaren-generated 100件、App-Reachable 100/100、privacy review PASS、exact/normalized 0、near review解決済みだけを許可する。
- privacy reviewは`pending = reviewer null / 全flag false`と`passed = Karen / 全flag true`の2形だけを許可し、部分的な自己申告を拒否する。
- `step3_only`は`nls3_batch_001`の100件manifestが`VALIDATED + frozen`になったときだけ発行する。
- Step 2時点のmanifestは`counts_toward_karen_minimum=false`であり、将来のreview/累積回帰前に1000件へ算入しない。
- invalid caseはID・理由・同batch内replacement IDを`invalid_case_history`へ残す。replacementはfinal corpusに存在する別IDでなければならず、registered / retired IDの再利用、別batch、同一ID置換を拒否する。
- replacement履歴を含むmanifest IDも全payloadから再計算し、履歴の後付け・差替えを検出する。

### 2.5 corpus registry / privacy

- 次の集合を混ぜずに登録した。
  - Karen-generated contract fixture
  - `invalid_contract`
  - `legacy_input`
  - `real_user_current_valid`（未受領、private-only）
- contract fixtureはbatch 000のrepo-safe syntheticだけに限定した。
- case ID、retired invalid ID、exact identity、normalized identityをcumulative novelty indexへ固定した。
- future batchはregistry内の既存repo-safe reviewed synthetic corpusもduplicate比較対象にする。
- invalid IDとreplacement IDの再利用を禁止し、次batchへ引き継ぐbody-free lineageを用意した。
- private sourceをshareable SHA-256 builderへ渡すと拒否する。
- private input/case/corpus用に、versioned domain-separated HMACを別APIとして用意した。
- raw実ユーザーcorpus、raw本文、unsalted private input hashをregistryへ置かない。

### 2.6 annotation leak guard

- generation input projectionは次の4fieldだけをdeep-copyする明示allowlistとした。
  - `thought_text`
  - `action_text`
  - `emotions`
  - `categories`
- case ID、batch ID、source、semantic contract、coverage、family、review情報はprojectionへ入らない。
- annotationを変更してもprojectionがbyte-equivalentであることを試験した。
- schema外annotationを持つcaseはprojection前に拒否する。

## 3. 独立試験

### Step 2

- direct dependency-free runner: **13 / 13 PASS**
- valid fixture: 4件
- independent invalid fixture: 16件
- legacy fixture: 3件
- batch 001 boundary: 99件RED / 100件PASS / 101件RED

主な独立negative:

- thought/actionの空・空白・ECMAScript trim境界
- emotion/category 0件、unknown、重複、非array
- 自己理解混在、自己理解strength不正
- schema外field、wrong version、ID/batch不一致、非bool
- duplicate JSON key、NaN/Infinity、BOM、CRLF、final LF欠落、invalid UTF-8、lone surrogate
- exact / normalized / near、near false-positive review、sample順反転
- coverage/registry/manifestの`True == 1`型混同攻撃
- forged artifact ref、state昇格、parent/file hash drift
- frozen validator / duplicate policyのprocess内hash drift
- invalid→replacementの同一ID、別batch、final corpus不在、registered / retired ID再利用、不正reason/status
- nested emotion type/strengthの非string入力
- private sourceの通常commitment/report/matrix流入
- test-only annotationのprojection流入

### Step 0/1 regression

- direct dependency-free runner: **11 / 11 PASS**
- Step 0/1 frozen artifacts: byte不変

環境には`pytest` packageがないため、schema libraryやpytestを追加していない。既存テスト関数を同じPython processで直接実行した。

## 4. 新規成果物とSHA-256

| ファイル | SHA-256 |
|---|---|
| `ai/tests/schemas/emlis_nls_v3_sample_case_v1.schema.json` | `90d569460f05aa7347145ba1562754c1304fe4b4878165b5bfbb1180cf9087ef` |
| `ai/tests/schemas/emlis_nls_v3_coverage_matrix_v1.schema.json` | `1e0f31277fd008759e221d0c60ce589ecaede74dfcd55f49002dccd0a68a5c4c` |
| `ai/tests/schemas/emlis_nls_v3_sample_batch_manifest_v1.schema.json` | `439a64bd457d547bb530922be0d6273d1415783c15fea31f1b618a924035cdae` |
| `ai/tests/schemas/emlis_nls_v3_corpus_registry_v1.schema.json` | `d28fe0045a393965c4637a320fa98fc1b23c632ca1dd75888a0925d9e61d6c62` |
| `ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py` | `cf4f048258c92ccad8d99ee8af4926f1a5730682ae772b9d44a16fc302ff9b6d` |
| `ai/tests/fixtures/emlis_nls_v3/contract/valid_v1.jsonl` | `0f5a6a25f93fb6ee4a155c6f85e51db828375a50667995d6af587941c1d020c0` |
| `ai/tests/fixtures/emlis_nls_v3/contract/invalid_v1.jsonl` | `d7cbc344701635d53da21ebb2814a9c8d814cf1c403392b506ece6c00e6e5b77` |
| `ai/tests/fixtures/emlis_nls_v3/contract/legacy_v1.jsonl` | `e61614561986f92ead55aa830e4c4a0e32932dfbc1fe4d02b7ba4cb9aa7b1db6` |
| `ai/tests/fixtures/emlis_nls_v3_s2_corpus_registry_20260714.json` | `7746ec94267fae0b89adbf8b5a676e469386fd3376275bc5197e39742941eb3d` |
| `ai/tests/test_emlis_nls_v3_s2_sample_registry.py` | `3ef4753f1f7cb24cbb73c96161d68fac189109da313c746736d46fb39f1ad3e9` |

この文書を含め、今回の変更はすべて新規ファイルである。production、RN、DB、public API、停止済みv2、既存Step 0/1成果物は変更していない。

## 5. 完了条件と次authority

Step 2の実owner、strict contract、positive test、独立negative test、parent/source hash、body-free registry receipt、completion conditionを固定した。

次に許可されるのは次だけである。

1. 華恋が既存registry/coverage/duplicate evidenceを読む。
2. `nls3_batch_001`の新規100件を作る。
3. validator、novelty、privacy reviewを通す。
4. `VALIDATED + frozen` manifestを作る。
5. その後にStep 3へ進む。

batch 001の100件作成はStep 2完了直後の移行作業であり、今回の完了件数へ含めていない。NLS v3 source、EmlisAI結果、runtime switch、release authorityはまだ存在しない。
