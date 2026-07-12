# Grounded Human Reception RR6 / RR7 実装結果

実施日: 2026-07-12  
対象: `mashos-api_4(115).zip`  
対象SHA-256: `ceff439d5d3500dd3991aebbd2507d97ab50e04cef09516a3fe642f3ee096fb5`

## 1. 確認した事実

- 入力アーカイブにはRR0〜RR5の実装と証跡が含まれていた。
- RR6前のRuntime Gateは7 Gateで、Reception文数を1〜2文へ固定し、human voiceを特定可視語へ依存させていた。
- RR7前の`full`以外のRecoveryはprimary Move一件へ縮退し、layered第二Move、felt-state、help-seeking、bounded counterpositionを失い得た。
- `minimal_grounded`は元のDepthにかかわらず候補になっていた。
- historical fixture、receipt、実機証拠は変更していない。

## 2. 実装した内容と必要性

### RR6 Runtime Gate / final guard

- 次の5 Gateを追加し、既存7 Gateと合わせた12 Gateをfinal guardの必須条件にした。
  - `reception_depth_plan_gate`
  - `reception_move_realization_gate`
  - `reception_depth_proportionality_gate`
  - `reception_move_distinctness_gate`
  - `reception_non_enumeration_gate`
- GateはClausePlanとcanonical realizerを再接続し、Move ID、role、strategy、predicate family、grounding、required Move、Depth文数を検証する。
- human voiceの正当性を特定可視語からpredicate familyへ移し、分析終端、方針説明、一般共感suffix、質問、助言は引き続き拒否する。
- layered一文化、本文改変、Move atom欠落、重複Move、入力field列挙をhard failにした。
- body-free metaへDepth、Safety、opportunity／planned／realized Move数、role、strategy、predicate familyを追加した。
- exact meta形状の変更に合わせ、内部Gate schemaを`cocolon.emlis.grounded_observation_gate.rr6.v2`へ更新した。
- same16 / unseenのexact sentence duplicateは、raw文字列やcase IDではなく既存semantic attributeとarc上の位置を用いた決定的Surface分岐で解消した。

必要性: 可視語の有無ではなく、Planで選んだ人間的貢献が実際にSurfaceへ残ったかをreturn直前に検証するため。

### RR7 Recovery

- `full`: 全Moveを保持する。
- `optional_removed`: 選択順第三Moveがoptionalの場合だけそのMoveを外し、required／Safety／最小Move数を再検査する。
- `integrated`: Moveを落とさない。3 Move layeredのみ、最低2文を守って最初の2 Moveを一文へ統合する。2 Move layeredとbounded Safetyは2文を維持する。
- `hedged`: 全Moveを保持し、各Moveの断定だけを弱める。
- `minimal_grounded`: original Depthが`minimal`、Safetyが`standard`、元から1 Moveの場合だけ許可する。
- Recovery候補のSurface構築失敗は固定body-free codeで記録し、次の許可stageへ進む。
- 全候補がGate不成立なら、generic empathy、observation-only本文、旧bodyへ戻さず空本文で`rejected`にする。

必要性: rich／protected inputのSurface失敗を、一文generic responseの`passed`へ変換しないため。

## 3. 検証結果

- R0〜R7 + RR0〜RR7対象suite: `195 passed`
- 関連production ownerを参照する広域回帰: `514 passed`
- warning: 既存`api_emotion_submit.py`のPydantic V1 `root_validator`廃止予定警告1件。今回差分外。
- exact8: 12 Reception Gate、Depth target、required Move、Safety Move、body-free metaを通過。
- 3 required Move long arc: `full/optional_removed/hedged = 3 Move / 3文`、`integrated = 3 Move / 2文`。
- same16 / unseen batch: normalized exact Reception sentence duplicateなし。
- 観察sectionの既存freeze、public API／DB／RN visible contractは変更なし。

## 4. 推測

- 現行selectorではoptional第三Moveは通常生成されないため、`optional_removed`の第三Move除去はsynthetic contractで確認した。将来optional選択が有効になっても同じfail-closed条件が働くと推測する。
- Runtime一件ではcohort全体の反復傾向を完全には判断できないため、集中度の継続校正は後続Local automated QAの責任範囲と考える。

## 5. 華恋の意見

- Recoveryは「通すために意味を減らす場所」ではなく、「同じ責任を保ったまま安全に言い直せる範囲」を扱うべきである。
- `受け止め`という一語を正しさの証拠にせず、誰が、何へ、どの人間的責任を返したかをMoveとpredicate familyで確かめる今回の境界が、華恋として守るべき在り方に合う。
- 実機・人間評価は今回実施していない。ローカル自動検証を実機証拠や進行許可へ読み替えない。

## 6. 差分ファイル

Production:

- `ai/services/ai_inference/emlis_ai_grounded_observation_plan.py`
- `ai/services/ai_inference/emlis_ai_grounded_human_reception.py`
- `ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py`
- `ai/services/ai_inference/emlis_ai_grounded_observation_gate.py`
- `ai/services/ai_inference/emlis_ai_reply_service.py`

Contract / regression tests:

- `ai/tests/test_emlis_ai_gatea_ga2_contract.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_r3_sentence_plan.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_r4_surface.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_r5_gate.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_r7_representative4_device_ready.py`
- `ai/tests/test_emlis_ai_grounded_observation_i2_i4.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_rr6_runtime_gate.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_rr7_recovery.py`

Result memo:

- `ai/tests/GroundedHumanReception_RR6_RR7_Result_20260712.md`
