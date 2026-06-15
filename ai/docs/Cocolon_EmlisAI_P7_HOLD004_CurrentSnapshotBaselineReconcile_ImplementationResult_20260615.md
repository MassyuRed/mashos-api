# Cocolon / EmlisAI P7-HOLD-004 Current Snapshot Baseline Reconcile 実装結果

作成日: 2026-06-15 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
成果物種別: Markdown実装結果doc  
対象: Cocolon / EmlisAI / P7 Product Quality Runner / Long-run Product Gate / P7-HOLD-004 / Current Snapshot Baseline Reconcile / R13-R20  
基準設計書: `Cocolon_EmlisAI_P7_HOLD004_CurrentSnapshotBaselineReconcile_DetailedDesign_ImplementationOrder_20260615.md`  
基準ローカルsnapshot: `mashos-api_5(70).zip`  
GitHub接続確認: Mash指定により不要。未実施。  
RN変更: なし。  
API route変更: なし。  
request key変更: なし。  
public response top-level key変更: なし。  
DB変更: なし。  
Emlis本文runtime変更: なし。  
Gate緩和: なし。  
`release_allowed`: false固定。  
`p7_complete`: false固定。  
`p8_start_allowed`: false固定。  
`hold004_close_allowed`: false固定。  
`full_backend_suite_green_confirmed`: false固定。  

---

## 0. この実装結果の結論

今回、P7-HOLD-004 Current Snapshot Baseline Reconcile のR13〜R20範囲を、current local snapshot基準で実装・確認した。

今回の到達点は次である。

```text
R13: Current Snapshot Baseline Reconcile materialを追加。
R14: active current collect baselineを20260615 currentへ更新。
R15: group inventoryをcurrent baselineへ更新。
R16: execution plan / minimal orderをcurrent baselineへ再接続。
R17: group run result / execution summaryのbaseline参照を更新。
R18: matrix consistency / hold matrix / release handoff / validation matrixをcurrent baselineへ再接続。
R19: refreshed baseline上のofficial group_02 capture採用条件を固定。
R20: implementation result doc / 前提資料反映候補を作成。
```

今回の実装は、P7-HOLD-004を閉じる実装ではない。  
今回の実装は、full backend suite greenを確認した実装でもない。  
今回の実装は、group_02のofficial capture runを実行・記録した実装でもない。

中心判断は次で固定した。

```text
古いbaselineを、current baselineとして扱わない。
collect-only成功を、execution greenとして扱わない。
wildcard passを、official group resultとして扱わない。
subset greenを、full backend suite greenとして扱わない。
```

---

## 1. 確認済みcurrent baseline

current active collect baselineは次である。

```text
baseline_id:
  p7_hold004_backend_collect_baseline_20260615

collect_command_id:
  pytest_collect_only_backend_20260615

source_snapshot_ref:
  mashos-api(147).zip

test files:
  425

collected tests:
  2856

warnings:
  1

test_items_fingerprint_sha256:
  fee1eca805564d0840dc5b23f60a7e2d6c7297d658a76dc4ce175e0137c261f1

test_files_fingerprint_sha256:
  6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6
```

previous baselineは次として保持した。

```text
baseline_id:
  p7_hold004_backend_collect_baseline_20260614

source_snapshot_ref:
  mashos-api(146).zip

test files:
  416

collected tests:
  2673

warnings:
  1

group_02_p7_hold004:
  10 files / 69 tests
```

差分は次である。

```text
test files delta:
  +9

collected tests delta:
  +183

warnings delta:
  0

affected_group_ids:
  - group_02_p7_hold004
```

---

## 2. R15/R16 current group inventory / execution plan

current group inventoryは、13 groups / 19 batchesを維持した。  
変更の中心は `group_02_p7_hold004` である。

```text
group_02_p7_hold004:
  file_count: 19
  test_item_count: 252
  timeout_budget_sec: 120
  planned_batch_count: 1
  batch_id: group_02_p7_hold004_batch_01
  batch_policy: single_batch_preferred
```

totalは次で固定した。

```text
group_count:
  13

total_batch_count:
  19

total_group_file_count:
  425

total_group_test_item_count:
  2856

unassigned_test_file_count:
  0

duplicate_assignment_count:
  0
```

execution plan / minimal orderは、次のcurrent idsへ再接続した。

```text
collect_baseline_id:
  p7_hold004_backend_collect_baseline_20260615

inventory_id:
  p7_hold004_backend_suite_group_inventory_20260615

execution_plan_id:
  p7_hold004_backend_suite_execution_plan_20260615

first_capture_group_id:
  group_02_p7_hold004
```

---

## 3. R17/R18 execution summary / matrix reconnect

execution summaryは次へ更新した。

```text
execution_summary_id:
  p7_hold004_backend_suite_execution_summary_20260615

source_snapshot_ref:
  mashos-api(147).zip
```

次のmatrix / handoff / validation materialは、同じcurrent baseline connectionを参照する。

```text
backend_suite_split_matrix
r10_hold_matrix
release_handoff
validation_matrix
matrix_consistency_report
minimal_order
```

current baseline connectionは次で固定した。

```text
collect_baseline_id:
  p7_hold004_backend_collect_baseline_20260615

group_inventory_id:
  p7_hold004_backend_suite_group_inventory_20260615

execution_plan_id:
  p7_hold004_backend_suite_execution_plan_20260615

execution_summary_id:
  p7_hold004_backend_suite_execution_summary_20260615

current_collect_file_count:
  425

current_collect_test_item_count:
  2856

group_02_file_count:
  19

group_02_test_item_count:
  252

old_baseline_id:
  p7_hold004_backend_collect_baseline_20260614

old_baseline_used_as_current:
  false
```

維持した境界は次である。

```text
full_backend_suite_green_confirmed=false
hold004_close_allowed=false
p7_complete=false
p8_start_allowed=false
release_allowed=false
```

---

## 4. R19 official group_02 capture採用条件

R19では、group_02 official capture runを実行したのではなく、採用条件をbody-free materialとして固定した。

採用ruleは次である。

```text
schema_version:
  cocolon.emlis.p7.hold004.official_group02_capture_adoption_rule.v1

adoption_rule_id:
  p7_hold004_group_02_official_capture_adoption_rule_20260615

group_id:
  group_02_p7_hold004

batch_id:
  group_02_p7_hold004_batch_01

run_kind:
  capture_run

collect_baseline_id:
  p7_hold004_backend_collect_baseline_20260615

inventory_id:
  p7_hold004_backend_suite_group_inventory_20260615

plan_id:
  p7_hold004_backend_suite_execution_plan_20260615

expected_group_file_count:
  19

expected_group_test_item_count:
  252

expected_collect_only_test_item_count:
  252

expected_warning_count:
  1

expected_timeout_budget_sec:
  120
```

採用条件は次である。

```text
1. collect baseline builderがcurrent 425 / 2856 / warnings 1である。
2. group inventory totalがcurrent collectと一致している。
3. group_02 inventoryが19 files / 252 testsである。
4. execution planのfirst_capture_group_idがgroup_02である。
5. group_02 collect-onlyが252 tests collectedである。
6. run result materialがcurrent baseline / current inventory / current planに接続している。
7. group_idはgroup_02_p7_hold004である。
8. batch_idはgroup_02_p7_hold004_batch_01である。
9. run_kindはcapture_runである。
10. terminal output / stdout / stderr / traceback bodyをmaterialへ入れない。
```

PASS採用条件は次である。

```text
status:
  PASS

observed_counts:
  passed: 252
  failed: 0
  skipped: 0
  warnings: 1
  errors: 0
  deselected: 0
```

PASSとして採用できても、主張可能なのは次だけである。

```text
can_claim_group_green=true
```

PASSとして採用できても、次はfalseのままである。

```text
can_claim_full_backend_suite_green=false
full_backend_suite_green_confirmed=false
hold004_close_allowed=false
p7_complete=false
p8_start_allowed=false
release_allowed=false
```

FAIL / TIMEOUT / COLLECTION_FAILED / INTERRUPTED は、official capture materialとして記録可能な結果だが、greenではない。  
FAILはfirst red classification、TIMEOUTはtimeout classification、COLLECTION_FAILED / INTERRUPTEDはexecution blockerとして扱う。

old baselineのrun resultはcurrent summaryへ採用しない。

```text
old collect_baseline_id:
  p7_hold004_backend_collect_baseline_20260614

R19 decision:
  REJECTED_BASELINE_MISMATCH
```

---

## 5. R19時点の実行状態

R19採用条件は固定したが、official group_02 capture runは未実行である。

```text
official_capture_run_executed=false
official_capture_result_recorded=false
official_group_02_capture_green_confirmed=false
group_run_results_recorded=false_or_summary_default
full_backend_suite_green_confirmed=false
```

補足:

```text
current zip上で過去に確認した group_02 wildcard 252 passed / 1 warning は、良い兆候ではある。
ただし、R19採用条件固定前のad hoc確認であり、official group resultとしては記録しない。
```

---

## 6. 検証結果

今回の実装範囲で確認した検証は次である。

```text
py_compile:
  OK

R13-R18 target tests before R19/R20:
  183 passed

R13-R20 target tests after R19/R20:
  183 passed

full collect-only after R19/R20:
  2856 tests collected
  1 warning

group_02 collect-only after R19/R20:
  252 tests collected
```

R19/R20では、新規test fileを追加していない。  
理由は、新規test fileまたは新規test functionを増やすと、current active collect baselineの `425 files / 2856 tests` 自体が変わるためである。  
R19の採用条件確認は、既存group result test内の既存test functionへassertを追加して行った。

---

## 7. 今回変更したファイル

```text
modified:
  mashos-api/ai/services/ai_inference/emlis_ai_p7_hold004_backend_suite_execution_results.py
  mashos-api/ai/tests/test_emlis_ai_p7_hold004_backend_suite_group_result_20260614.py

added:
  mashos-api/ai/docs/Cocolon_EmlisAI_P7_HOLD004_CurrentSnapshotBaselineReconcile_ImplementationResult_20260615.md
```

---

## 8. 前提資料反映候補

次回、Cocolon_前提資料へ反映する場合の候補flagsは次である。

```text
p7_hold004_current_snapshot_baseline_reconcile_r13_r20_reflected: true
p7_hold004_current_backend_collect_baseline_id: p7_hold004_backend_collect_baseline_20260615
p7_hold004_current_backend_collect_baseline_file_count: 425
p7_hold004_current_backend_collect_baseline_test_count: 2856
p7_hold004_current_backend_collect_warning_count: 1
p7_hold004_current_backend_test_items_fingerprint_sha256: fee1eca805564d0840dc5b23f60a7e2d6c7297d658a76dc4ce175e0137c261f1
p7_hold004_current_backend_test_files_fingerprint_sha256: 6866231daf68427dca2de1b2011feea49450f7b4a8b3c5b9dec0f9ccd5f3e9c6
p7_hold004_previous_backend_collect_baseline_id: p7_hold004_backend_collect_baseline_20260614
p7_hold004_previous_backend_collect_baseline_file_count: 416
p7_hold004_previous_backend_collect_baseline_test_count: 2673
p7_hold004_previous_backend_collect_warning_count: 1
p7_hold004_backend_collect_baseline_delta_file_count: 9
p7_hold004_backend_collect_baseline_delta_test_count: 183
p7_hold004_backend_collect_baseline_delta_warning_count: 0
p7_hold004_current_group_02_file_count: 19
p7_hold004_current_group_02_test_count: 252
p7_hold004_backend_group_count: 13
p7_hold004_backend_total_batch_count: 19
p7_hold004_backend_group_execution_started: false
p7_hold004_backend_group_run_results_recorded: false
p7_hold004_official_group_02_capture_adoption_rule_fixed: true
p7_hold004_official_group_02_capture_run_executed: false
p7_hold004_official_group_02_capture_result_recorded: false
p7_hold004_official_group_02_capture_green_confirmed: false
p7_hold004_backend_full_backend_suite_green_confirmed: false
p7_hold004_backend_hold004_close_allowed: false
p7_complete: false
p8_start_allowed: false
release_allowed: false
```

前提資料反映時の注意は次である。

```text
- 旧baseline 416 / 2673を消さず、previous baselineとして保持する。
- current baseline 425 / 2856をactive currentとして扱う。
- group_02 252 passedのad hoc確認をofficial resultへ昇格しない。
- R19は採用条件固定であり、official capture run実行ではない。
- full backend suite green未確認を維持する。
```

---

## 9. 未確認

```text
- official group_02 capture run。
- official group_02 capture resultの実記録。
- split group全体のexecution結果。
- full backend suite execution green。
- first red / first timeoutの実観測。
- 実機submit / modal読感。
- P5 human Blind QA。
- P6 limited visible expansionの人間読感。
- P8 user model / dictionaryへ進める条件。
```

---

## 10. 書かれていない

```text
- R13-R20完了でP7-HOLD-004が閉じた、とは書かれていない。
- current collect-only 2856 collectedをfull backend suite greenとして扱ってよい、とは書かれていない。
- group_02 252 passedのad hoc確認をofficial resultとして扱ってよい、とは書かれていない。
- matrix consistency PASSをrelease readyとして扱ってよい、とは書かれていない。
- P8を開始してよい、とは書かれていない。
- release_allowedをtrueにしてよい、とは書かれていない。
```

---

## 11. 推測禁止

```text
- baseline差分を環境差分や誤差として流さない。
- collect-only成功を実行greenと扱わない。
- wildcard passをofficial group resultと扱わない。
- subset greenをfull backend suite greenと扱わない。
- R19採用条件固定をofficial run実行済みと扱わない。
- old/current baseline idを曖昧にしない。
- timeoutやwarningを根拠なく無害扱いしない。
- P7-HOLD-004を閉じたと断定しない。
- P8へ進めると断定しない。
- release readyに近づいたと商品判断しない。
```

---

## 12. 次に実行すべきこと

次工程は、R19で固定した採用条件に基づいて、group_02 official capture runを実行するか判断することである。

実行候補は次である。

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference \
  pytest -q --tb=short -p pytest_asyncio.plugin tests/test_emlis_ai_p7_hold004_*.py
```

採用するときは、次を必ず守る。

```text
- refreshed baseline / inventory / planと一致していることを確認する。
- PASSしてもgroup greenのみとする。
- FAIL / TIMEOUT / COLLECTION_FAILED / INTERRUPTEDはbody-free official capture materialとして記録し、greenにしない。
- terminal output / stdout / stderr / traceback bodyをmaterialへ入れない。
- full_backend_suite_green_confirmed=falseを維持する。
```

