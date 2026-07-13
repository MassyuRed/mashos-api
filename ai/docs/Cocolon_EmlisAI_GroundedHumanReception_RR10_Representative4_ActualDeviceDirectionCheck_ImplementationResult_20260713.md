# Grounded Human Reception RR10 代表4件・実機方向確認 実装結果

作成日: 2026-07-13  
対象入力: `mashos-api_7(91).zip`  
現在状態: ローカル実行準備完了／実機未実行  
次の実行者: Mash様  
進行権限: `none`

## 1. 結論

RR10のローカル側責任として、最新RR8 / RR9 sourceへ拘束した代表4件の期待packet、実機証拠template、body-free readiness、構造不足・期待hash不一致を拒否するcontract test、参照された証拠ファイルを再計算するbundle verifierを実装した。

production codeは修正していない。RR8 / RR9で固定した可視本文、Depth、Move、Gate、API / DB / RN境界が現行sourceで成立しており、RR10は外部実機表示とMash様読感を確認する段階だからである。

実機操作、生backend body取得、画面確認、Mash様Product Read Feelはローカルだけでは生成できない。したがってRR10 actual-device PASSは未確定であり、RR11、P5、P6、P8へ進む権限を与えていない。

## 2. 確認した事実

- 入力アーカイブSHA-256: `78d8ad3c938c9cd6a13f4e27627ea7ec093caf4f10d5be8e70a1c73ed21c4064`
- RR10を実際に定義する添付設計書SHA-256: `bef049a1751e636dc05bc065c90e297ab5bded23208bfd52523f8e36ae0c22f4`
- 現行source snapshot SHA-256: `ed9d7463778909c97115096345d25d6ce260d21ed737a72d7c06ccd8e08687ac`
- RR8 technical acceptance: PASS
- RR9 華恋local Product Read Feel: human PASS
- RR10代表4件は順番を含めて `A → B → I6-L03 → I6-D02`。
- 旧R7代表4件は `I6-S03` を含み、B / I6-D02も修復前の本文hashである。RR10の証拠として流用していない。
- 既存実機画像・ログは修復前surfaceの履歴証拠であり、現行RR10 hashとの一致を示さない。

| case | 確認責任 | expected visible SHA-256 | depth | moves / sentences |
|---|---|---|---|---|
| A | short inputを水増ししない | `2831eced030b599096412135efa356e01fb7b532b557c0643ff8860bcc53c054` | minimal | 1 / 1 |
| B | long multi-relationを選択的な二文へ広げる | `e12ade7fd87d00278c5ad1a605ab4b4d233243689a086d78e67ad35b8a8dd9a8` | layered | 2 / 2 |
| I6-L03 | intention / uncertainty / actionを選択的な二文へする | `fe4159a54168beda4451091d3b2eadf85f1156e5b441891566d0f5af7508e253` | layered | 2 / 2 |
| I6-D02 | safety Moveを保持する | `3c8a58c67f7d87dd1e9d782cbfab30d03bdd7f72c98aebeec02884223dc5b39a` | focused | 2 / 2 |

## 3. 実装した契約

### expected packet

次を一つの実行正本へ固定した。

- exact8 fixtureとcase identity
- app-validな感情強度・感情／カテゴリ選択順
- RR8 receipt、RR9 visible packet、RR9華恋receipt
- source snapshot
- 代表4件の順序、選定理由
- visible / observation / reception section hash
- Depth、Opportunity、planned / realized Move、sentence count
- reception Gate 12項目とruntime guard 4項目
- 実機環境、取得必須証拠、完了条件、停止条件

### actual-device evidence template

実機結果はexpected packetを変更せず、templateの複製へ記録する。未実行template自身は全case `not_run` であり、画面、hash、Mash判定を先取りしていない。

実機PASSを受理するにはcaseごとに次が必要である。

- exact current input identity
- 実際の感情強度・感情／カテゴリ選択順と入力選択画面
- request payload参照・ファイルSHA-256・canonical current input SHA-256
- backend response参照・ファイルSHA-256・`input_feedback.comment_text`・`observation_status`
- 実行時刻、app build、deploy identity、device / OS / app version
- request trace identity
- 実backendの生 `input_feedback.comment_text` 参照
- 生本文をUTF-8として計算したfull / observation / reception SHA-256
- body-free Gate meta参照とSHA-256
- Gate metaから再取得したDepth、Opportunity、planned / realized Move、sentence count
- modal screenshot参照とSHA-256
- 二段表示、observation回帰、Depth、clipping、重なり、scroll、安全境界の判定
- §17.12に対応するMash様6軸判定と総合PASS / FAIL

自動GateをMash様判定へ転用することは禁止している。

### validator

次を拒否するcontractとbundle verifierを追加した。

- source、fixture、RR8 / RR9証拠hashの不一致
- case欠落、重複、順序違反
- backend生body以外、OCR、手入力転記を本文hash根拠にすること
- full / section hash不一致
- request traceの使い回し
- raw body、Gate meta、screenshotのないPASS
- request payload、raw body、Gate meta、screenshotの参照先不存在・危険な相対path・ファイルhash不一致
- request payloadから再計算したcurrent input hash不一致
- app-valid選択順・強度と実機記録の不一致、入力選択画面ファイルhash不一致
- backend responseの不存在、file hash不一致、public path / status不一致、抽出bodyとの不一致
- raw comment bytesから再計算したfull / section hash不一致
- Gate meta本文混入、12 Gate / 4 runtime guard不合格、Depth / Move / sentence実測値不一致
- B / I6-L03のmodal先頭・末尾証拠不足
- Depth、表示、layout、安全、Mash軸の一項目でも未PASSの状態でのPASS
- 自動判定をMash様判定として扱うこと
- 4 / 4成立前のRR11実機証拠収集許可
- RR10だけを根拠にP5 / P6 / P8または進行権限を開くこと

bundle verifierは、与えられた証拠ファイルの存在とbytes整合を検査する。実機を操作した事実や取得元の真正性そのものを自動的に証明するものではないため、build / deploy identity、request trace、実機画面の取得はMash様が保持する。

## 4. Mash様に必要な実機作業

順番を変えず、1件ずつ行う。

```text
A
B
I6-L03
I6-D02
```

各caseの実行手順:

1. exact8 fixtureの選択順、強度、改行、句読点を変えずに入力し、送信前の選択画面を撮影する。
2. `/emotion/submit` へ送ったcurrent input JSONと実backend responseを保存する。
3. `input_feedback.comment_text` だけを末尾改行等も加えずUTF-8ファイルへ保存する。OCR・手入力転記は使わない。
4. section hashは `split_two_stage_surface` と同じ規則で計算する。LF単位で分割し、label行を除外し、section内部をLFで再結合して `.strip()` したUTF-8本文をhashする。
5. backendで得た `grounded_observation` のbody-free Gate meta objectだけをJSON保存し、request trace、build / deploy identityも保存する。生本文をGate meta JSONへ混ぜない。
6. RNの `Emlisの観測` modalを撮影する。A / I6-D02は全体、B / I6-L03は少なくとも先頭と末尾を連続して残す。
7. 二段順序、切れ、重なり、scroll不能、Depth target、安全境界を確認する。
8. 次の6軸を自動結果とは別にMash様自身が判定する。
   - 淡泊に見えない
   - 長い入力へ十分に留まっている
   - 全情報を順番に処理した感じがない
   - 同じ言葉・骨格の使い回しに見えない
   - Emlisの反応として自然
   - short inputが水増しされていない

1件でもFAILならそのcaseを `failed`、後続caseを `not_run` のままにして停止し、`first_failed_case_id` と `mismatch_codes` を残す。submit errorやbackend response未取得のように本文・modalまで到達できない場合は `blocked` とfailure stageを記録し、取得済みのinput / trace証拠だけを保存して同様に停止する。validatorはFAIL / BLOCK自体を有効な非進行証拠として受理する一方、失敗後の実行とRR11許可を拒否する。local / device hashが異なる場合は、expected hashを都合よく更新せず、deploy lineage、runtime source、public response bodyを再確認する。

実機後はtemplateを上書きせず複製し、実際の証拠参照と判定を記入する。すべての参照は証拠bundle rootからの安全な相対pathにし、次でbytes整合を確認してから証拠ファイル一式とともに華恋へ返す。

```bash
python tools/emlis_grounded_human_reception_rr10_verify_device_evidence.py \
  tests/local_only/grounded_human_reception_rr10_representative4_expected_packet_20260713.json \
  <実機結果receipt.json> \
  <証拠bundle root>
```

## 5. 推測

- ユーザー指定の `DistinctnessRepair` 原本は今回の添付物に存在しない。RR10章を持つ `ResponseDepth_RichnessRepair` 設計書は前者を基礎設計と明記しているため、今回の後続正本と判断した。
- local runtimeとRR9 packetが一致することは、実機でも一致する必要条件である。しかしproduction deploy、通信経路、RN表示を単独では証明しない。

## 6. 華恋の意見

- RR10で重要なのは「画面に出たらだいたい同じ」ではなく、入力identity、backend生body、可視hash、Depth、画面の読み心地を一つの実行へ結び付けること。
- Aの短さとB / I6-L03の厚みは、文字数の差ではなく、受け取れる意味機会の差として実機でも見える必要がある。
- I6-D02は文量だけでなく、苦しさを否定せず、自己否定へ同意せず、助けへ残した行動を失わないことを画面上でも確認したい。
- RR10の4件PASSはRR11 exact8証拠収集を始める条件であり、R8全体の進行判断そのものではない。

## 7. 現在の固定状態

```text
actual_device_status = not_run
next_required_owner = mash_actual_device_operator
rr11_exact8_actual_device_allowed = false
p5_formal_24_start_allowed = false
p6_start_allowed = false
p8_start_allowed = false
progression_authority = none
valid_for_progression = false
```
