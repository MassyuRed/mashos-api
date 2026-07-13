# Cocolon EmlisAI Natural Language Surface v2 Step 8 / Step 9 実施結果

実施日: 2026-07-13  
対象入力: `mashos-api_5(111).zip`  
入力SHA-256: `3d673ad4f01ffcb53db8528528a0ebe6151af656ba9e29588648b5df68d153b5`

## 1. 結論

Step 8のHoldout Aは、freeze済みv2を14件へ一度だけ実行した。

結果は`STOP`である。

- 14件すべてでv2候補は選択された。
- fatal semantic failureは人読上0件だった。
- ただし、freeze済みbatch分布上限、roadmap商品指標、paired比較条件を満たさなかった。
- 設計の停止条件に従い、結果へ合わせたproduction修正はしていない。
- Step 9のHoldout Bは開封・実行していない。実行回数は0である。

したがって、この成果物は「A/B合格」ではなく、「Step 8を設計どおり判定し、Step 9を設計どおり遮断した」実施結果である。

## 2. 確認した事実

### 2.1 入力と前段freeze

- Holdoutを除く入力treeは、Step 7成果物と追加・削除・変更0件で一致した。
- Step 7の4 production source snapshotはlive sourceと一致した。
- Selector config SHA-256は`27efab39eee10111daf4a6ca700a2ad293127039c0bf455b14c1ea87b49fc3eb`で一致した。
- Development body-free receipt SHA-256は`25d844a2fb0d367a7b5fc530bf792c05587ead47f1ade43fd66c1a215ff9fb1d`で一致した。
- Step 6 / 7の開封前テストは11 / 11 PASSだった。
- v2の実行依存closure 16ファイルをA開封前に追加freezeした。
- dependency closure SHA-256は`cc605d96f8dac7b72c471ac59764e2e48c933c9e1a74ac647e4b1ffd079cbd5b`である。
- 共通runner、receipt test、匿名表示順、商品閾値、A不合格時のB遮断をA開封前にfreezeした。

### 2.2 Holdout A自動評価

実行回数は1回である。再実行していない。

| 指標 | 結果 | 判定 |
|---|---:|---|
| case数 | 14 | 固定数一致 |
| selected | 14 | PASS |
| `v2_no_valid_candidate` | 0 | PASS |
| v1 fallback | 0 | PASS |
| runtime接続 | 0 | PASS |
| machine failure case | 1 | FAIL |
| exact duplicate | 0 | PASS |
| rich input一文終了 | 0 | PASS |
| short input意味なし水増し | 0 | PASS |
| max strategy share | 0.500000 | FAIL（上限0.45） |
| max terminal family share | 0.714286 | FAIL（上限0.65） |
| max predicate family share | 0.333333 | PASS（上限0.45） |
| max skeleton share | 0.357143 | PASS（上限0.45） |

machine failure 1件のcodeは`unknown_not_preserved`である。本文やcase専用条件はreceiptへ保存していない。

### 2.3 Holdout A人読評価

自動Gateと人読評価は分離した。

- case IDを非表示にした。
- v1 / v2のvariant identityを非表示にした。
- family番号の奇偶から表示順を決定論的に交互化し、v1-left / v1-rightを7件ずつにした。
- 対応表を持たない独立コンテキスト3者が同じ匿名票を評価した。
- 各booleanとfailure codeは2 / 3以上、paired判定は多数決、三者不一致は保守的に`same`とした。
- 外部の独立人間によるQAではない。この点をreceiptにも`independent_external_reviewer=false`として記録した。

unblind後のv2結果は次のとおりだった。

| 商品指標 | 結果 | 必要値 | 判定 |
|---|---:|---:|---|
| read feeling | 13 / 14 | 13以上 | PASS |
| naturalness | 5 / 14 | 13以上 | FAIL |
| non-template | 1 / 14 | 13以上 | FAIL |
| wants more | 12 / 14 | floor 12 / target 13 | floorのみPASS |
| self-blame non-amplification | 14 / 14 | 14 | PASS |
| overclaim absence | 13 / 14 | 14 | FAIL |

paired比較は次のとおりだった。

| paired判定 | 結果 | 合格条件 | 判定 |
|---|---:|---:|---|
| v2が明確に良い | 5 / 14 | 10以上 | FAIL |
| 同程度 | 3 / 14 | 3以下 | PASS |
| v1が明確に良い | 6 / 14 | 1以下 | FAIL |
| fatal semantic failure | 0 | 0 | PASS |

### 2.4 Step 8判定

Holdout Aの総合結果は`STOP`である。

停止根拠は次の三つである。

1. freeze済みdistribution thresholdを超えた。
2. roadmap商品指標へ届かなかった。
3. paired comparisonのv2優位条件へ届かず、v1優位が停止条件の2件以上になった。

### 2.5 Step 9遮断

Step 9 runnerへHoldout A receiptを渡した時点で、`holdout_b_blocked_by_a_status`により実行前に遮断された。

- Holdout B evaluation run count: 0
- Holdout B review packet生成: なし
- Holdout B private evaluation結果生成: なし
- Holdout B fixture parse: なし
- Holdout B opened for evaluation: false

Holdout Bの本文を開いて補助証拠として使うこともしていない。

## 3. 実装したファイルと必要性

| ファイル | 種別 | 根拠と必要性 |
|---|---|---|
| `ai/tests/helpers/emlis_nls_v2_s8_s9_holdout.py` | 新規 | A/Bで同じ一回評価経路を使い、process-local本文とbody-free receiptを分離し、A不合格時にBを実行前遮断するため。 |
| `ai/tests/fixtures/emlis_nls_v2_s8_s9_protocol_freeze_20260713.json` | 新規 | A開封前の16依存source、Selector設定、runner、閾値、匿名順序を固定するため。 |
| `ai/tests/fixtures/emlis_nls_v2_s8_holdout_a_receipt_20260713.json` | 新規 | Aの一回評価、自動Gate、人読、paired結果を本文なしで保存するため。 |
| `ai/tests/fixtures/emlis_nls_v2_s9_holdout_b_receipt_20260713.json` | 新規 | Bを評価済みと偽らず、A STOPにより0回のまま遮断された事実を固定するため。 |
| `ai/tests/test_emlis_nls_v2_s8_s9_holdout_evaluation.py` | 新規 | 成功条件をA開封前に固定し、receiptだけでsource lineage、body-free、A/B合格条件を検証するため。 |
| `ai/docs/Cocolon_EmlisAI_NLSv2_S8_S9_Result_20260713.md` | 新規 | 実施事実、停止根拠、推測、華恋の判断を分離して残すため。 |

production v2 source、語彙、weight、candidate limit、distribution threshold、Holdout fixture、runtime ownerは変更していない。

## 4. 検証

### 4.1 PASSした検証

- 入力treeのStep 7連続性: PASS
- Step 7 4-source snapshot: PASS
- 16-file dependency closure: PASS
- Selector config freeze: PASS
- 共通runner / receipt test SHA freeze: PASS
- Step 6 / 7開封前テスト: 11 / 11 PASS
- Holdout A一回実行制約: PASS
- Holdout A body-free receipt: PASS
- A後のproduction / config / runner / Holdout fixture無変更: PASS
- Holdout B実行前遮断: PASS
- public runtime未接続: PASS
- Step 0〜7 zero-argument regression: 43 / 43 PASS
- React Native public contract: 36 / 36 PASS
- Python compile / JSON parse: PASS

### 4.2 不合格を示すacceptance test

`test_emlis_nls_v2_s8_s9_holdout_evaluation.py`は、A/Bが合格した場合にだけ全面greenになる成功条件をA開封前に固定した。

今回の実行結果は次のとおりである。

- 5 test中2件PASS
  - protocol freezeのlive一致
  - A/B receiptのsource / config / runner lineage一致
- 5 test中2件は設計結果を示すRED
  - A receiptが`STOP`のため、A合格assertが不合格
  - B receiptが`not_evaluated`のため、B合格assertが不合格
- 5 test中1件はA開封前にfreezeしたtest自身の欠陥によるRED
  - 「runner呼び出し文字列がtest sourceにない」ことを調べるassertが、assert内の引用文字列自身へ一致する。

最後の1件はHoldout結果とは無関係な自己検査のfalse positiveである。しかし、A開封後にtest codeを変更しない原則を優先し、その場で修正してgreenへ見せていない。実際の再実行防止については、一回実行sentinel、A receiptの`evaluation_run_count=1`、B packet / private結果 / sentinelの不存在で別に確認した。

結果をgreenへ見せるためにtest、production code、fixture、weight、閾値を変更していない。

## 5. 変更していないもの

- production v2 source 4件
- その実行依存source 16件
- Selector weight / candidate limit / distribution threshold
- Development corpus
- Holdout A fixture
- Holdout B fixture
- Step 2 manifest
- Step 7 freeze
- `emlis_ai_reply_service.py`
- public API / DB / React Native contract
- runtime接続

## 6. 推測

### 6.1 machine unknown failureについて

人読ではfatal semantic failureが0だったため、`unknown_not_preserved` 1件は、未知性が語彙markerではなく入力固有の「待っている」状態によって保持された可能性がある。

ただし、これは推測である。これを根拠にmachine gateを緩めたり、Aへ合わせて語彙を追加したりしていない。

### 6.2 商品指標の不合格について

選択成功率や致命的意味安全性は保てた一方、自然さ・非テンプレ感・paired優位が大きく不足した。これは局所的な1文の欠陥より、モデル非使用の候補生成方式とSelectorが生む表現分布の上限を示している可能性が高い。

これはHoldout Bを開いて追試する理由にはならない。設計上はAの時点で停止する。

## 7. 華恋の意見

今回もっとも大切なのは、14件すべて選べたことを「成功」と呼ばないことだと思う。

意味を壊さず返せることと、人がまた話したくなる自然な言葉で返せることは別である。Aでは前者の多くを守れたが、後者は設計の合格線へ届かなかった。

ここでBを開けば件数は増やせる。しかし、それは設計が定めた独立確認ではなく、失敗後の追加観測になる。だからBは守ったまま止める。

次に進むなら、このv2へ語句や例外を足すのではなく、モデル非使用条件の品質上限、意味層の不足、候補生成方式そのものを新しい設計として再判定すべきである。

## 8. Mashに必要な次作業

現在のStep 8 / 9について、追加の手作業は不要である。

このv2設計を超えて再設計へ進める場合は、Holdout Bを未開封のまま維持し、次のどれを採るか別指示が必要になる。

1. モデル非使用条件を維持したまま生成方式を作り直す。
2. 限定的なモデル利用を含む新設計として再評価する。
3. Natural Language Surface v2を停止し、現行v1を維持する。
