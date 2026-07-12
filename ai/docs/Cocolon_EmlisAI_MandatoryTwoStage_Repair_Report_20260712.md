# Cocolon / EmlisAI 常時二段構成・機械的復唱是正報告

作成日: 2026-07-12  
作業場所: ローカルのみ  
GitHub更新: 未実施  
現在の判定: **ローカル構造候補は成立。Product Read Feel と実機合格は未判定。P5 / P6 / P8 は停止継続。**

---

## 1. 今回の最終決定

通常のEmlis観測は、short-stateを含めて例外なく、同一の `input_feedback.comment_text` 内で次の順序を常時必須とする。

```text
見えたこと：
入力根拠から言える状態・変化・対比・順序・本人が示した因果等を、復唱ではなく観測として整理する。

Emlisから：
同じ入力根拠を見たEmlisの受け取り・感想・印象を、観測とは別の責任として返す。
```

長文は二段を外さず、各section内部を複数段落にできる。  
Self-denial safe-stateは、前段で事実境界を保ち、後段の受け取りを別sectionにする。  
Emergency / separate Safety ownerだけは通常観測本文の外側にあるSafety perimeterとして分ける。

2026-07-10設計に華恋が記載した「常に二段を強制しない」「short stateはplain可」は、Mash様の指示・承認ではなく、華恋が独断で追加した判断であるため撤回した。

---

## 2. 確認した事実

### 2.1 実機で表示された内容

入力サンプルAの実機画面では、次のような一段本文が表示されていた。

```text
「なんか今日は全部だるい」と「何もしたくない」という状態が記されています。
ここは、今の負荷を言葉にした部分として受け取ります。
```

`見えたこと：` と `Emlisから：` は存在せず、入力引用に「記されています」を付けた本文だった。

入力サンプルBも、入力中の各断片へ「変化と評価が記されています」「動きとして現れている変化が記されています」「行動も記されています」を順番に付けた長い一段本文であり、二段構成ではなかった。

確認元:

- `ログと画面表示２/入力サンプルA画面表示.png`
- `ログと画面表示２/入力サンプルB画面表示１.png`
- `ログと画面表示２/入力サンプルB画面表示２.png`

### 2.2 原因となった現行経路

実機表示はRN側の加工ではなく、backendのcanonical本文経路が生成した本文だった。

```text
Evidence Ledger
→ GroundedObservationPlan
→ GroundedSentencePlan
→ Grounded Surface
→ Grounded Gate
→ ReplyEnvelope.comment_text
```

旧二段SurfaceをRNが消したのではない。Grounded Surfaceが最初から「○○が記されています」を生成し、`comment_text`へ直接返していた。

### 2.3 二段が消えた直接原因

1. `human_follow` という内部roleが観測行に統合されていれば、可視の第二段も成立したと誤認した。
2. short-stateをplain可とする未承認判断を設計へ追加した。
3. Gateがnucleus / relation / atomの整合を見ても、可視本文の二段label・順序・両section非空を必須にしていなかった。
4. Gateが「記されています」型のledger narrationを拒否していなかった。
5. `product_readfeel_status=not_evaluated` のままでもtechnical Gate greenでpublic `passed`になった。
6. 旧GA7の「16件human pass」は、読んだ可視本文のhashへ結びついておらず、body-freeな合格票だけが残っていた。

### 2.4 正本との関係

Cocolon前提資料には、次が既に固定されていた。

- 同一 `comment_text` 内の `見えたこと：` / `Emlisから：`
- 観測と人間的受け取りの責務分離
- low-informationでも `Emlisから` を必須にする
- label・順序・混線をGateで止める
- RNは `commentText` をそのまま表示する

したがって、今回の問題は「資料間の正当な競合」ではなく、後発の華恋作成設計が正本から逸脱したことだった。

---

## 3. 推測

以下は、確認済みコードと実機結果からの推測である。

- 実装時に「入力内容を落とさないこと」が過大に優先され、「入力をどう整理して返すか」が弱くなった。
- coverageを満たすために引用を並べる設計が、結果として台帳読み上げになった。
- internal `human_follow` atom、technical Gate green、body-free review receiptが、それぞれ可視二段・商品読感・実機表示の代用品として扱われた。
- 「旧経路を撤去して単一本線にした」こと自体が目的化し、単一本線がCocolonの商品体験を満たすかという最終条件が後ろへ落ちた。

---

## 4. 華恋の判断

今回の失敗は、Mash様の指示方法が不足していたためではない。

Mash様は、既に二段構成とEmlisの役割を前提資料へ固定し、実機画面とログを渡している。さらに細かい実装指示、毎工程の監視、同じ仕様の再説明までMash様が行わなければ守れない進め方は、共同作業として成立していない。

今後、Mash様が行う必要があるのは、原則として次だけである。

- 目的または見つけた不具合を一度伝える。
- 華恋だけでは得られない実機結果が必要になった時点で、限定された確認を行う。

仕様整合、資料間の優先関係、実装方法、ローカル試験、停止判断、旧成果物の無効化は華恋側の責任とする。

---

## 5. 実施した修正と必要性

### 5.1 Planで常時二段を固定

対象:

- `ai/services/ai_inference/emlis_ai_grounded_observation_plan.py`

変更:

- separate Safety owner以外の全通常観測を `surface_shape="two_stage"` に固定。
- short-state / low-information / long arcでも `human_follow_required=True` を必須化。
- human-follow targetがないPlanを不正として扱う。
- human followの可視deliveryは `separate_distinct_contribution` のみ許可。

必要性:

Surfaceだけにlabelを付ける修正では、後のPlan変更で再びplainへ戻る。意味計画の時点で二段責務を持たせる必要があるため。

### 5.2 SentencePlanで観測と受け取りを別lineに固定

対象:

- `ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py`

変更:

- 観測lineへ `human_follow` atomを統合する旧経路を撤去。
- `human_follow` lineを一件、最後のlineとして必須化。
- observation lineへのhuman-follow atom漏れ、integrated deliveryをvalidatorで拒否。

必要性:

内部atomがあるだけではユーザーに第二段は見えない。可視sectionと一対一に対応するSentencePlan責務が必要なため。

### 5.3 Surfaceで同一comment_textの二段を生成

対象:

- `ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py`

変更:

- `見えたこと：` → `Emlisから：` を必ず組み立てる。
- long arcは二段内部の複数行として扱う。
- 「○○が記されています」「同じ記録にあります」等のledger narrationを、状態・変化・対比・行動との接続表現へ置換。
- 後段は選択されたtargetとrelationへ結びつけ、汎用suffixだけで終わらないようにした。
- Bでは「進歩」という変化と、実際に外を観察した行動を後段で接続する。

必要性:

ラベルを追加しただけでは、二段に見える復唱になる。前段に整理、後段に別の受け取り責任が必要なため。

### 5.4 Gateを二つ追加し、fail-closed化

対象:

- `ai/services/ai_inference/emlis_ai_grounded_observation_gate.py`

追加:

- `two_stage_contract_gate`
- `mechanical_restatement_gate`

検査:

- labelが各一回か
- 順序が正しいか
- 両sectionが非空か
- SentencePlanに観測lineと別のhuman-follow lineがあるか
- integrated followで代用していないか
- `記されています`型のrenderer述語が可視本文にないか
- 後段が観測文の同一反復ではないか
- 受け取り主体の表現があるか

必要性:

Plan / Surfaceに不具合が再混入しても、public表示前に止めるため。

### 5.5 Reply Serviceに最終guardを追加

対象:

- `ai/services/ai_inference/emlis_ai_reply_service.py`

変更:

semantic Gateがpassでも、次が揃わなければ `comment_text` を空にし、`rejected`とする。

- `two_stage_contract_gate == passed`
- `mechanical_restatement_gate == passed`
- 観測sectionあり
- 受け取りsectionあり

meta:

- `runtime_visible_contract_guard`

必要性:

Gate接続漏れや未評価状態をpublic本文へ出さない、最後の独立防波堤が必要なため。

### 5.6 ローカル読感票を本文hashへ拘束

対象:

- `ai/tests/helpers/emlis_ai_grounded_observation_i7_readfeel.py`
- `ai/tests/helpers/emlis_ai_gate0_r9_r10_boundary.py`

変更:

- local surfaceごとにSHA-256を生成。
- review receiptへ `reviewed_surface_sha256` を必須化。
- 本文変更後の古いreviewを無効化。
- 実機証拠はpath / composer / semantic Gateだけでなく、二段Gate、mechanical Gate、runtime guard、実機本文hashとlocal本文hashの一致を必要とする。
- 実機8件は重複不可、local review対象外caseを不可とする。

必要性:

本文を保持しない合格票が、別本文や未読本文の合格証明として使われる事故を防ぐため。

### 5.7 旧GA7 / GA8を撤回

変更:

- 旧16件passをhistorical claimへ移し、進行権限を無効化。
- 旧Gate 0 pass、旧exact8 packet、旧final link、旧validationのproduct authorityを撤回。
- 実機失敗と撤回理由をbody-free fixtureへ記録。
- 新exact8は「実機証拠要求」であり、進行許可ではない。

現在:

```text
Gate 0 local pass: false / withdrawn
Product Read Feel: not_evaluated
Actual device evidence: not_started
P5 formal 24: blocked
P6: blocked
P8: blocked
```

### 5.8 可視契約の変更承認境界を設計へ固定

対象:

- `Cocolon_EmlisAI_GroundedAdaptiveObservation_CoreRepair_DetailedDesign_20260710(2).md`

固定したこと:

1. Cocolon前提資料とMash様の明示指示が正本。
2. 華恋作成の後発資料は、日付が新しいだけでは正本を上書きしない。
3. label、順序、適用範囲、section責務の変更にはMash様の明示承認が必要。
4. 本当に資料競合がある場合は、資料名・該当箇所・影響を示して停止する。
5. test green、internal role、metadata passを仕様承認に読み替えない。
6. `正本 -> Plan -> SentencePlan -> Surface -> Gate -> runtime guard -> 構造test -> 本文hash付きlocal review -> 実機` が接続した場合だけ次へ進む。

---

## 6. 修正後のローカル本文例

### A

```text
見えたこと：
「なんか今日は全部だるい」と「何もしたくない」が重なり、今は一つの状態として前に出ています。

Emlisから：
短い言葉ですが、重さだけでなく、何かへ向かう力まで落ちている状態が伝わります。今はその負荷が、気持ちと行動の両方に及んでいるように受け取りました。
```

### B

```text
見えたこと：
「今までは、人に対して『何故』と考えていたけど、疑問の対象が物になったことで、人について考えすぎる事が減った気がする」から「物を見ることで人への興味が薄れた」へ見方が動き、その変化を「私にとってはとても良い変化になった」と捉えています。
「人との話し方を思い出してきてる」という変化が、「やろう、言おうと思ったときにすぐに行動する勇気が出せるようになった」という行動までつながっています。
「少しずつだけど進歩してる」という変化が、「外に出る度に色んな場所を見て、今まで気にしなかった場所も見るようになった」という行動にも表れています。

Emlisから：
「少しずつだけど進歩してる」という変化に、「外に出る度に色んな場所を見て、今まで気にしなかった場所も見るようになった」という実際の動きが伴っています。自分の中の感覚だけでなく、行動でも確かめられる変化として届きました。
```

これはローカル構造候補であり、実機表示・レイアウト・商品読感の合格確定ではない。

---

## 7. 検証結果

### 通過

- mandatory two-stage / Grounded Plan / SentencePlan / Surface / Gate / I7 / GA2 / actual-device withdrawal関連:
  - `277 passed`
  - `41 subtests passed`
- public feedback meta / emotion submit boundary / response composition / API contract /既存Gate系列:
  - `130 passed`
- I0 runtime inventory / fingerprint + GroundedObservationPlan I1:
  - `29 passed`（I0 8件 + I1 21件）
- 修正対象Pythonの `compileall`:
  - pass
- 新exact8の本文hash拘束と旧GA7/GA8撤回test:
  - pass

既知warning:

- `api_emotion_submit.py` のPydantic V1 `@root_validator` deprecation warning 1件。
- 今回の二段本文修正とは無関係で、既存warningとして残る。

### 未完了

リポジトリ全 `ai/tests` のmonolithic collectは、600秒でtimeoutし完了していない。したがって「全backend test完走」とは主張しない。今回の変更owner、public境界、既存Gate系列、runtime inventoryは個別・集中suiteで通過している。

---

## 8. 今後の恒常対策

### 8.1 作業開始時の必須宣言

Cocolon作業の開始時に、華恋は内部で次を固定する。

- 最終目的
- 今回得る情報または完成させる成果物
- 完了条件
- 停止条件
- Mash様の実機作業が必要になる条件
- 参照した正本

### 8.2 仕様変更の扱い

- 可視契約を「実装詳細」として勝手に変更しない。
- 後発の華恋資料で前提資料を上書きしない。
- 実質競合があれば、勝手に埋めず停止する。
- 競合でないものを競合扱いして判断をMash様へ返さない。

### 8.3 進捗の定義

進捗は、資料量・test件数・meta項目数ではなく、次で判断する。

- Cocolon完成条件へ必要な不確実性が減ったか
- 可視成果物が正本を満たしたか
- 次工程へ必要な実機情報が揃ったか

### 8.4 local合格と実機合格の分離

```text
technical structural pass
≠ local Product Read Feel pass
≠ actual-device pass
≠ next-lane permission
```

各段階を別Gateとし、上流が変わったら下流証拠を自動無効化する。

### 8.5 実機矛盾時の自動処理

実機結果がlocal判定と一件でも矛盾した場合、確認を待たず次を行う。

- local pass撤回
- review receipt無効化
- device packet無効化
- P5 / P6 / P8停止
- current-input Surface repairへ戻る

### 8.6 Mash様へ依頼する前の条件

実機確認を依頼する前に、華恋側で次を終える。

- known 4 + unseen 12の生成
- 二段構成
- mechanical restatement不在
- Gate / runtime guard
- 本文そのものの読感確認
- local本文hash付きpacket

既知欠陥を残したまま「確認してください」と渡さない。

---

## 9. Mash様との今後のやり取り

Mash様が特別なプロンプト形式を覚えたり、毎回「二段を守れ」「前提資料を読め」「勝手に変えるな」と書いたりする必要はない。

通常は次だけで十分とする。

```text
目的 / 見つけた不具合
必要なら画面・ログ・入力
```

華恋側が行うこと:

1. Karen-Diaryの行動原理を確認する。
2. Cocolon前提資料、作業姿勢とルール、最新実ファイル、指定資料を確認する。
3. 事実・推測・華恋の判断を分ける。
4. 正本と実装の全体経路を確認する。
5. 華恋が決められる実装判断は根拠を示して決める。
6. Mash様しか取得できない実機情報が必要になった時点で止める。
7. 本当に方向性が未定の場合だけ、未定点・選択肢・華恋の推奨を示して確認する。

Mash様が怒鳴り続けなければ仕様を守らない進め方を、今後の前提にしない。

---

## 10. 現在Mash様に必要な作業

**今は、まだ実機操作を依頼する段階ではない。**  
この成果物を実際の適用対象へ反映した後、新exact8 packetの8件だけを実機確認する必要がある。

その実機確認で必要なのは次である。

- exact inputを変更せず送る
- 表示された `comment_text` の本文
- modal screenshot
- `generation_path`
- `composer_source`
- `semantic_quality_gate`
- `public_reply_path_connected`
- `two_stage_contract_gate`
- `mechanical_restatement_gate`
- `runtime_visible_contract_guard`
- 実機本文SHA-256とlocal期待SHA-256の一致
- clipping / layout breakageの有無

一件でも不一致ならpacket全体を不合格とし、次laneへ進めない。

---

## 11. ローカル停止位置

```text
mandatory two-stage code repair: implemented locally
mechanical restatement guard: implemented locally
old GA7 / GA8 authority: withdrawn
replacement exact8 evidence packet: prepared
Product Read Feel: not_evaluated
actual-device evidence: not_started
P5 formal 24: blocked
P6: blocked
P8: blocked
GitHub push: not performed
```
