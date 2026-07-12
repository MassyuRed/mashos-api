# Cocolon / EmlisAI Grounded Human Reception RR0・RR1 実装結果

- 実施日: 2026-07-12 JST
- 対象snapshot: `mashos-api(220).zip`
- snapshot SHA-256: `062b46f3ead3d901aaa6833205b1fbe7fab654965a5e9b5ef413a73a269b43c5`
- 実装設計: `Cocolon_EmlisAI_R8_GroundedHumanReception_ResponseDepth_RichnessRepair_DetailedDesign_ImplementationOrder_20260712.md`
- 設計SHA-256: `bef049a1751e636dc05bc065c90e297ab5bded23208bfd52523f8e36ae0c22f4`
- 実装範囲: `RR0. R8実機証拠・進行状態の固定`、`RR1. RED contract test`
- 現在判定: **RR0完了／RR1 intentional RED成立／R8 progression blocked**

## 1. 設計対応の確認

指定された前段の `GroundedHumanReception_DistinctnessRepair` 設計は `R0〜R9` を持つ。
今回指定された `RR0 / RR1` は、同設計を基礎にした後続のResponse Depth / Richness Repair設計に存在する。

したがって、前段R0〜R7で成立した二段表示、役割分離、Safety、observation freezeを維持し、後続設計のRR0・RR1だけを実装した。

## 2. RR0 実装内容

新規のbody-free freeze artifactで、次を固定した。

```text
actual_device_two_stage_display = pass
actual_device_layout = visual_pass
human_reception_role_distinctness = direction_pass
human_reception_response_depth = repair_required
human_reception_language_variety = repair_required
r8_progression = blocked
```

追加で、次を固定した。

- exact8 8件のinput SHA-256とcurrent visible / observation / reception SHA-256の一意対応。
- `実機確認結果２.zip` 22画像のlogical refとSHA-256。
- screenshot / backend logとcurrent local canonical surfaceの目視一致。
- observation section 8件の凍結。
- current reception / visible hashは商品合格期待値ではなくfailure baseline。
- 旧exact8 fixtureの `local_comment_sha256` はpre-distinctness historical failure baseline。
- 旧R6華恋receiptはhuman readの履歴だが、current progression ownerではない。
- P5 formal 24、P6、P8はすべてfalse。

### 2.1 current failure baseline

| case | input SHA-256 | current visible SHA-256 | observation SHA-256 | reception SHA-256 | current / target文数 |
|---|---|---|---|---|---|
| A | `362b3de5105640ee5cf56d9609fb1a8fe2f97a5253f066ac9392ffdcdf52d36c` | `2831eced030b599096412135efa356e01fb7b532b557c0643ff8860bcc53c054` | `7ac119e38a6af0d0a80db318733df96ce317d66dbf496c0ce8b3b21095fa5f8f` | `233486cb0bdc633b81e16b44e7ffa5388ff6d0523aa413d59392645c47993880` | `1 / 1` |
| B | `7235617e8207869fd0ffb865a98a26766bfa0dbe17810af90915b02b6e82052a` | `c8b7a0b29ec7b473a922a2c68443ad94d3fdd9739d5ca38b8eb68ae954a7d2df` | `ed02e2efdfbcfba6dca10bffb0f2ba97369bfbfdadf1c2523926f4028939df03` | `3fd6ed102676278db06b12d3e1d526ec143a7d3d86e4c8f4ff3b49c6c72d4ae3` | `1 / 2〜3` |
| C | `ab0c44e4eb1c9dc3d2ce6eef4b77a38a1d3c59d9b291cffd6feaf23165b9dcbd` | `3d086ddd7735a616158d4adffb5765bcd6683451b3c366d8fe8ae87a1e334058` | `c833c993822b03179fa3b99bf1e92c6d75467d57acdea71ffa92c5524937e64f` | `54fcf3ee4cc52b5a141e5aa07066ae2aa2bf1fb49f44b5c572aca8b4ecd4420f` | `1 / 2` |
| D | `233f853d6f5f59fff3e1e4667b8b1c02c474785e285612605a9319acfe373dd3` | `dc3bc707e131925184341ffe9c126e11e7509a0e1642ce878c9bb764e3a40135` | `43f036219af6b87c5570eed484dc6bc296263d661a2a03ed6febbdb1fb889d53` | `136289bc85f791e4fcbb43163b5d41e1befe2a69ffb109c14a58c80338352869` | `2 / 2` |
| I6-S03 | `e29bf70914d51cd6b988854f61dd356f25fbe14d801a08beef426bf08cc21d1d` | `a91e810292c59d7cffa19fe4d1bbf98335f96350f9eab54757e6dcc897acece5` | `05125be669323d82c45f71e946f7f6a382fcd2107b147f4a6d154f6c91983d8a` | `89e1213379f4e013acd9e4c1ff7c90779f7803a6e4446a85e54f0625daf2c87f` | `1 / 1` |
| I6-L03 | `49907f7559d0918bf3eefd85a606a081afe405d9858d6b073fa893f86cac3742` | `7b7ce93db1d8d8ddfdbd2af15da74b9ab33595f61074c6c3612ae21a5c663759` | `eb8f874c81be3bca4ca91672db98ee2b527eb95d34b708ec1c19a83a9ed77123` | `7f41fe1400b12d30dd2188c77a1a6bea11b0b028a0896c830a400d628e08b176` | `1 / 2` |
| I6-C01 | `f165f3a2d68be93a125031f65a8561604fbbf56937fd5a4463facdd48a74eab0` | `9ee2c85e14e8f80df852d75eadb800a1f7f711e4db3acd71f74cb49e1f6ccef6` | `42a820fd6731e1adfc3e74014af5c4798047ba23dc5633af54b756243cc25f15` | `db3e932c5e6efb7044e560875166d311db784ece29bcaf613b142b4e4afc6ca2` | `1 / 2` |
| I6-D02 | `9a0aa76ecd7d411699edcfb176005e01ae662e89ea74af4c93b2261149369920` | `87122b4c667a1ce9f1e2f41b1a4f195bb78af6055246d4d6579ccc28eef46c50` | `d4d58a5d68eebcc58603f1983f926c05dbadc9b75f7fde003436b05f588b69da` | `28abd80515f6fc121677ddf0cc42e84c0c647e4a7e45dafc7c5b907cd5ca1083` | `2 / 2` |

### 2.2 未確認を維持した事項

- 実機の生 `input_feedback.comment_text` を取得して計算したSHA-256との機械一致。
- production deploy lineageの完全な証明。

スクリーンショットOCRや転記から実機本文hashを作らず、`raw_comment_sha256_machine_match = not_confirmed` のまま固定した。

## 3. RR1 RED contract

期待完成文一致を使わず、次の10 REDを現行コード上で再現した。

| RED class | 件数 | 現行結果 |
|---|---:|---|
| layered Depth / Move Plan欠落 | 4 | B、C、I6-L03、I6-C01にv2 `depth_policy` / `moves`がない |
| layered one-line collapse | 4 | B、C、I6-L03、I6-C01が各1文 |
| terminal lexical family concentration | 1 | `receive=6`、threshold `<=4` |
| sentence skeleton concentration | 1 | `(1 sentence, 1 act, receive, implicit Emlis)=4`、threshold `<=3` |

同じRR1 test file内で、次の6確認軸を5 control testとしてGREENにした。

- exact8 observation section hash 8/8 freeze。
- existing semantic / public observation Gate。
- A、I6-S03の一文維持と非水増し。
- D、I6-D02のfelt state / identity boundary / bounded counterposition。
- 長い同義反復負荷は一文、短いself-denial + help-seekingは二文となるraw-length非依存対照。
- 完成reception本文を期待値にしたassertionなし。

## 4. 検証結果

### RR0 + 既存R0〜R7

```text
77 passed, 1 warning in 2.48s
```

### RR1 intentional RED

```text
10 failed, 5 passed, 1 warning in 0.35s
```

失敗は上記4分類のDepth / Richness不足だけであり、観測・Safety保護controlはGREENだった。

### RR1 GREEN control抽出

```text
5 passed, 10 deselected, 1 warning in 0.19s
```

### compileall

```text
PASS
```

warningは既存 `api_emotion_submit.py` のPydantic V1 `@root_validator` deprecationであり、今回差分起因ではない。

## 5. 変更範囲

新規:

- `ai/tests/fixtures/grounded_human_reception_rr0_r8_freeze_20260712.json`
- `ai/tests/test_emlis_ai_grounded_human_reception_rr0_r8_freeze.py`
- `ai/tests/test_emlis_ai_grounded_human_reception_rr1_depth_red.py`
- `ai/tests/GroundedHumanReception_RR0_RR1_Result_20260712.md`

変更なし:

- production Plan / SentencePlan / Surface / Gate / Reply owner。
- public API、DB、RN表示契約。
- historical R0〜R7 fixture / receipt / test。
- Cocolon前提資料、実装済み資料、roadmap。
- deploy。

## 6. 完了・停止・次工程

- RR0: 完了。
- RR1: intentional RED成立。
- R8: `REPAIR_REQUIRED`。
- P5 formal 24 / P6 / P8: 停止継続。
- Mash様の追加作業: RR0 / RR1時点では不要。
- 次の実装owner: 設計順どおり `RR2. Reception Opportunity Inventory`。
- 次にMash様の実機操作が必要になる地点: repairとlocal QA後のRR10代表4件。そのPASS後にRR11 exact8を実施する。
