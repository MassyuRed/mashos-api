---
title: "R54-AHR Post-PNT Closed Material Next Boundary Confirmation PCM R8 Selected Regression Result"
created_at: "2026-07-08 JST"
source_mode: "local_received_zip_only"
github_connection_check: "not_required_by_Mash_instruction / not_performed"
phase: "P7 Product Quality Runner / Long-run Product Gate continued"
validated_range: "R8 / selected regression after PCM target validation"
code_change: "none"
test_change: "none"
result_memo_added: true
api_change: "none"
db_change: "none"
rn_change: "none"
runtime_change: "none"
response_key_change: "none"
json_schema_file_creation: "none"
pnt_op08_material_synthesis: "none"
selected_post_nci_next_boundary_execution: "none"
selected_pcm_next_boundary_execution: "none"
dhr_op05_call: "none"
dhr_op05_builder_call: "none"
dhr_op06_call: "none"
dhr_op07_materialization: "none"
dmd_execution: "none"
r52_actual_execution: "none"
actual_review_start: "none"
actual_rows_creation: "none"
question_need_observation_rows_creation: "none"
p8_start: "none"
p8_question_design: "none"
question_text_materialization: "none"
full_backend_suite_green_claim: "none"
rn_contract_green_claim: "none"
rn_real_device_verification_claim: "none"
p7_complete: "none"
release_decision: "none"
body_free: true
---

# R54-AHR Post-PNT Closed Material Next Boundary Confirmation PCM R8 Selected Regression Result

## 0. Scope

R8 records the selected regression for the local PCM implementation state.

```text
target:
  P7-R54-AHR Post-PNT Closed Material Next Boundary Confirmation
  PCM-OP00〜PCM-OP08 plus selected PNT / NCI / RDB / MRB / DRI / ELR regression set

result_memo_added:
  tests/R54_AHR_PostPNT_ClosedMaterialNextBoundaryConfirmation_PCM_R8_SelectedRegression_Result_20260707.md

not_changed:
  helper code
  regression tests
  API / DB / RN / runtime / response keys
```

R8 is validation only. It does not execute selected post-NCI or selected PCM boundaries and does not promote any candidate to downstream execution.

## 1. Selected regression command

```bash
cd mashos-api/ai

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_op01_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707.py \
  tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_result_20260707.py \
  tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op00_op01_20260706.py \
  tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op02_op03_20260706.py \
  tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op04_op05_20260706.py \
  tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_op07_20260706.py \
  tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_result_20260706.py \
  tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_op01_20260705.py \
  tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_op03_20260705.py \
  tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_op05_20260705.py \
  tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_op07_20260705.py \
  tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_result_20260705.py \
  tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py \
  tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705.py \
  tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py \
  tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py \
  -p no:cacheprovider
```

## 2. Result

```text
selected_regression:
  426 passed
```

## 3. Boundary preserved

```text
preserved:
  PNT selected handoff-or-stop boundary remains body-free
  PCM closed-material confirmation remains body-free
  all-lane target green is not converted to current lane
  next design candidate is not converted to DHR-OP05 call permission
  actual review not started
  P8 question design not started
  full backend / RN / real-device green not claimed
  P7 complete / release not claimed
```

## 4. Next

```text
next_required_step:
  R9 compileall
```
