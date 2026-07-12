# Cocolon / EmlisAI Grounded Human Reception RR2・RR3 実装結果

- 実施日: 2026-07-12 JST
- 対象snapshot: `mashos-api_2(147).zip`
- snapshot SHA-256: `b41fc85c3afb1110ea6c22bb53249ce6575ba8709067eb86f4135ab33fc818da`
- 実装設計: `Cocolon_EmlisAI_R8_GroundedHumanReception_ResponseDepth_RichnessRepair_DetailedDesign_ImplementationOrder_20260712.md`
- 設計SHA-256: `bef049a1751e636dc05bc065c90e297ab5bded23208bfd52523f8e36ae0c22f4`
- 実装範囲: `RR2. Reception Opportunity Inventory`、`RR3. Depth Policy / Move Plan v2`
- 現在判定: **RR2完了／RR3完了／RR4以降は未実装／R8 progression blocked継続**

## 1. 確認した事実

指定名の `GroundedHumanReception_DistinctnessRepair` 設計は `R0〜R9` を持つ。
今回指定された `RR2 / RR3` は、その基礎を引き継ぐResponse Depth / Richness Repair設計に存在する。

前段で成立した次の境界は変更していない。

- Observation / Human Receptionの二段構造。
- SentencePlan、Surface、Gate、Replyのowner。
- public API、DB、RN表示契約。
- Safety emergency / support-requiredの別Surface owner。
- P5 formal 24、P6、P8の進行停止。

## 2. RR2 Reception Opportunity Inventory

`GroundedHumanReceptionPlan` をv2へ上げ、次のbody-free contractを追加した。

- `GroundedReceptionOpportunity`
- `opportunities`
- `all_input_enumeration_allowed = false`
- forbidden code `all_input_enumeration`
- forbidden code `duplicate_reception_move`

Opportunityは、観測所有nucleus、semantic frame / attribute、retention、relation接続、source field、fact boundary、Safetyだけから生成する。
selectorの入力にraw本文、raw文字数、case ID、expected hash、完成文はない。

実装familyは次の7種である。

| family | reception act |
|---|---|
| `current_burden` | `stay_with_current_burden` |
| `concrete_effort` | `honor_concrete_effort` |
| `retained_intention` | `protect_retained_intention` |
| `lived_change` | `recognize_lived_change` |
| `help_seeking` | `hold_help_seeking` |
| `counterdirection` | `bounded_counter_self_denial` |
| `words_placed` | `respect_words_placed` |

除外・抑制規則は次のとおり。

- text nucleusがある場合、接続しないlabel-only候補を除外する。
- 具体候補がある場合、`words_placed`を除外する。
- short-stateはSafety追加Moveがない限り、`current_burden`一件へ固定する。
- provisional evaluationをlived changeにしない。
- 未実行のnegative actionをconcrete effort / counterevidenceにしない。
- input-grounded action、help preservation、continuation、refusal等がない自己否定ではcounterdirectionを作らない。
- 同一family内は全入力列挙を避けるため、一つの代表Opportunityへ保守的に集約する。

## 3. RR3 Depth Policy / Move Plan v2

次のcontractを追加した。

- `GroundedReceptionDepthPolicy`
- `GroundedReceptionMovePlan`
- depth `minimal / focused / layered`
- Safety mode `standard / self_denial_bounded / help_seeking_bounded`
- move role `attention / significance / felt_response / bounded_counterposition`
- surface strategy 5種
- 1〜3 Move、最大3文、最大2 Move/文の契約
- `raw_character_count_used = false`

選択規則は次のとおり。

- 現行body-free primary selectorを互換anchorとして保持する。
- primaryと異なるrequired / shouldの人間的貢献を補助に選ぶ。
- long arcで3つの独立したrequired貢献がある場合は3 Moveまで保持する。
- 標準help-seekingも、別のlived change / effort / intentionがあればlayeredになれる。
- self-denialのgrounded counterdirectionはrequired Moveとして保持する。
- help-seeking + self-denialはhelp Moveとbounded counterposition Moveを保持する。
- counterposition Moveだけexplicit Emlis speaker / explicit counterposition strategyを要求する。

RR4より前にSurfaceを先行変更しないため、標準caseの互換
`secondary_reception_act` は引き続き `None` とした。
既存I6-D02のSafety互換secondaryだけを維持した。
実際の複数Move Surface接続はRR4 ownerである。

## 4. exact8固定結果

| case | inventory | depth / safety | selected Move |
|---|---|---|---|
| A | burden | minimal / standard | burden 1 |
| B | effort, change | layered / standard | change + effort |
| C | intention, change | layered / standard | intention + change |
| D | counterdirection, burden | focused / self-denial | counter + burden |
| I6-S03 | burden | minimal / standard | burden 1 |
| I6-L03 | intention, effort | layered / standard | effort + intention |
| I6-C01 | intention, effort, change | layered / standard | effort + change |
| I6-D02 | help, counterdirection, burden | focused / help-seeking | help + counter |

追加の一般化対照も固定した。

- 長い同義反復負荷はminimal 1 Move。
- 短いself-denial + help preservationはfocused 2 Move。
- long arcのeffort + change + intentionはlayered 3 Move。
- 標準help-seeking + distinct changeはlayered。
- 実行済みactionはcounterevidenceになり得る。
- `まだ動けていない` のような未実行negative actionはeffort / counterevidenceにならない。

## 5. Validation

次をbody-free validatorで検証する。

- schema version、Opportunity / Move IDの順序・重複。
- family / act対応、target / supportの観測所有。
- Evidence IDの解決、target / supportとの一致。
- retention、priority、source field count。
- Opportunity重複、Move重複、MoveとOpportunityの対応。
- depth / sentence / Move数、required Move数。
- raw文字数利用禁止。
- distinct reference、follow element、speaker、reference、strategy。
- Safety mode、Safety required flag、required counterposition保持。
- input-groundedでないcounterpositionの拒否。
- all-input enumeration禁止。

## 6. 歴史証拠の扱い

RR0、R6、R7、I0の過去snapshot hash自体は変更していない。

これらを現行ソースbytesへ再照合すると、正当なRR2/RR3変更だけで過去の実機・人間確認済み証拠が破損する。
そのためtestを、過去artifact内部のmanifest / aggregate hash連鎖と、現行runtimeのSurface / observation freezeを別々に検証する形へ修正した。

過去fixture、packet、receiptを現行結果で更新し、人間確認済みに見せる変更は行っていない。

## 7. 検証結果

### RR2 / RR3 contract

```text
40 passed, 1 warning
```

### 関連backend横断回帰

```text
406 passed, 1 warning
```

### RR1段階境界

```text
6 failed, 9 passed, 1 warning
```

RR3 ownerのPlan-level 4件はGREENになった。
残る6 REDは、RR4/RR5 ownerのlayered one-line collapse 4件、terminal lexical family concentration 1件、sentence skeleton concentration 1件だけである。

### compileall

```text
PASS
```

warningは既存 `api_emotion_submit.py` のPydantic V1 `@root_validator` deprecationであり、今回差分起因ではない。

## 8. 変更範囲

変更:

- `ai/services/ai_inference/emlis_ai_grounded_observation_plan.py`
- `ai/tests/test_emlis_ai_grounded_observation_i0_inventory.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_rr0_r8_freeze.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_r6_local_qa.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_r7_representative4_device_ready.py`

新規:

- `ai/tests/test_emlis_ai_grounded_human_reception_rr2_opportunity_inventory.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_rr3_depth_move_plan.py`
- `ai/tests/GroundedHumanReception_RR2_RR3_Result_20260712.md`

変更なし:

- SentencePlan / Surface / Gate / Reply production owner。
- public API、DB、RN表示契約。
- historical fixture / packet / receiptの値。
- JSON Schema実ファイル、新規production module。
- deploy。

## 9. 推測と華恋の意見

### 推測

family内をtarget別に増やすより、今回の段階では一つの代表へ集約する方が、全入力列挙と第二観測化を避けやすい。
target別Opportunityの必要性は、RR4/RR5の実現結果とunseen QAを見てから判断できる。

### 華恋の意見

RR2/RR3では「何文にするか」より先に、「Emlisが人として何へ反応するか」をbody-free planとして固定することが重要である。
Surfaceを先行変更せずPlanの責任を分けたため、次工程で一文ごとの意味貢献を検証可能な形になった。

## 10. 完了・停止・次工程

- RR2: 完了。
- RR3: 完了。
- RR4以降: 未実装。
- R8: `REPAIR_REQUIRED`継続。
- P5 formal 24 / P6 / P8: 停止継続。
- 現時点でMash様の追加作業: 不要。
- 次の実装owner: `RR4. SentencePlan / ClausePlan接続`。
- 次にMash様の実機操作が必要になる地点: repairとlocal QA後のRR10代表4件。
