---
title: "R54-AHR PostPCM DHR-OP05 Manual Handoff Boundary / DHB R8 Selected Regression Result"
created_at: "2026-07-09 JST"
author: "華恋"
source_zip: "mashos-api_7(88).zip"
source_mode: "local_received_zip_only"
github_connection_check: "not_required_by_Mash_instruction / not_performed"
result_scope: "R8 selected regression"
selected_regression_file_set_green_confirmed: true
selected_regression_execution_mode: "split_by_design_list_group_after_one_shot_timeout"
selected_regression_total_passed_count: 583
code_change: "none"
test_change: "yes / existing Post-PNT PCM regression fixture intake repaired without production behavior change"
api_change: "none"
db_change: "none"
rn_change: "none"
runtime_change: "none"
response_key_change: "none"
dhr_op05_call: "none"
dhr_op05_builder_call: "none"
dhr_op06_call: "none"
dhr_op07_materialization: "none"
dmd_r52_execution: "none"
actual_review_start: "none"
actual_rows_creation: "none"
question_need_observation_rows_creation: "none"
p8_question_design: "none"
p7_complete: false
release_decision: "none"
---

# R54-AHR PostPCM DHB R8 Selected Regression Result

## 0. 結論

R8 selected regressionは、設計書に列挙された対象ファイルセットを分割実行し、全対象がgreenであることを確認した。

```text
R8 selected regression file-set split confirmation:
  583 passed
```

内訳は次の通り。

```text
DHB target files:
  258 passed

Post-PNT PCM boundary files:
  140 passed

Post-NCI PNT boundary files:
  122 passed

Post-ELR19 DHR-OP04/OP05 and DHR-OP06/OP07 vicinity files:
  63 passed

Total:
  583 passed
```

一括R8 commandも試行したが、この実行環境では完了前にtimeoutした。assertion failureではなく完了前timeoutであり、green countを一括結果としては主張しない。そのため、本memoでは、同じ設計対象ファイルセットを4 groupへ分けて実行し、各groupのgreenをもってR8 selected regression file-set greenとして記録する。

既存Post-PNT PCM regressionでは、一部テストがpytest collection時に上流PNT-OP08 materialを再materializeしていたため、fresh適用環境でcollectionが重く止まりやすかった。R8ではproduction helperを変更せず、test側に `r54_ahr_post_pnt_pcm_compact_pnt_op08_fixture_20260708.py` を追加し、PCM regression testsが契約validなbody-free PNT-OP08 closure fixtureを明示入力として使う形へ最小修正した。

この修正は、DHB helper、PCM production helper、PNT production helper、DHR-OP05 builder、API / DB / RN / runtime / response keyには触れていない。DHR-OP05 call / DHR-OP05 builder call / downstream executionの許可でもない。

## 1. 最小修正内容

追加・修正したtest側ファイルは次の通り。

```text
new:
  tests/r54_ahr_post_pnt_pcm_compact_pnt_op08_fixture_20260708.py

modified:
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_op01_20260707.py
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_op03_20260707.py
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_op05_20260707.py
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_op07_20260707.py
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py
```

修正意図は次だけである。

```text
- collection-timeの重い上流PNT-OP08 material生成を避ける
- PCM regressionが求める explicit closed PNT-OP08 material をbody-free fixtureとして渡す
- PNT-OP08 contract validを維持する
- production helper / runtime behavior は変更しない
```

## 2. 一括selected regression attempt

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_op01_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_op03_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_op05_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_op07_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_op01_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_result_20260707.py \
  tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py \
  tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py \
  -p no:cacheprovider
```

Observed result:

```text
one-shot selected regression: timeout before completion
assertion failure observed before timeout: none
one-shot passed_count: not claimed
```

## 3. Split selected regression confirmation

### 3.1 DHB target files

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py \
  tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py \
  -p no:cacheprovider
```

Result:

```text
258 passed in 4.92s
```

### 3.2 Post-PNT PCM boundary files

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_op01_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_op03_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_op05_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_op07_20260707.py \
  tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py \
  -p no:cacheprovider
```

Result:

```text
140 passed in 3.47s
```

### 3.3 Post-NCI PNT boundary files

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_op01_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_result_20260707.py \
  -p no:cacheprovider
```

Result:

```text
122 passed in 18.74s
```

### 3.4 Post-ELR19 DHR vicinity files

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain \
  tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py \
  tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py \
  -p no:cacheprovider
```

Result:

```text
63 passed in 1.42s
```

## 4. このmemoで主張しないこと

```text
- one-shot selected regression command completion
- full backend suite green
- RN contract green
- RN real-device green
- DHR-OP05 call allowed
- DHR-OP05 builder call allowed
- DHR-OP06 / DHR-OP07 / DMD / R52 allowed
- actual review start allowed
- P8 question design allowed
- P7 complete
- release ready
```

## 5. R8 closure

```text
selected_regression_file_set_green_confirmed: true
selected_regression_total_passed_count: 583
selected_regression_execution_mode: split_by_design_list_group_after_one_shot_timeout
production_code_changed: false
test_fixture_repair_changed: true
full_backend_suite_green_confirmed: false
rn_contract_green_confirmed: false
rn_real_device_modal_verified_claimed_here: false
dhr_op05_call_allowed_here: false
dhr_op05_builder_call_allowed_here: false
next_required_step: R9_compileall
```
