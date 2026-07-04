---
title: "Cocolon / EmlisAI P7-R54-AHR Post-PMN23 Downstream Manual Decision Hold Evidence Intake DMH-OP12/OP13 Result"
created_at: "2026-07-02 JST"
author: "華恋"
work_mode: "共鳴構造モード"
source_mode: "local_received_zip_only"
github_connection_check: "not_required_by_Mash_instruction"
implementation_scope: "DMH-OP12 question need observation rows normalization / DMH-OP13 rating-question consistency and blocker separation"
api_changed: false
db_changed: false
rn_changed: false
runtime_changed: false
response_key_changed: false
public_response_top_level_key_added: false
body_full_packet_generation: "not_run"
actual_local_human_review_execution: "not_run"
actual_operation_receipt_created_here: false
actual_rows_created_here: false
actual_rating_rows_created_here: false
actual_question_need_observation_rows_created_by_real_operation_here: false
actual_disposal_purge_execution: "not_run"
p5_finalization: false
p6_start: false
p8_start: false
p8_question_design: false
p8_question_implementation: false
r52_actual_execution: false
p7_complete: false
release_decision: false
---

# Cocolon / EmlisAI P7-R54-AHR Post-PMN23 Downstream Manual Decision Hold Evidence Intake DMH-OP12/OP13 Result

## 1. 実装範囲

今回進めた範囲は、次の2工程に限定した。

```text
DMH-OP12: question need observation rows normalization
DMH-OP13: rating-question consistency / blocker separation
```

この実装は、P7/P8 Bridge用のbody-free観察材料を受け、rating側の修正・安全・読感・実行blockerをP8候補へ逃がさないためのinternal helper boundaryである。

## 2. 事前確認

受領した `mashos-api_7` に、前回納品したDMH-OP10/OP11までの実装が含まれていることを確認した。

```text
previous_delivery_checked: Cocolon_EmlisAI_P7_R54AHR_PostPMN23_DMH_OP10_OP11_NewAndModifiedFiles_20260702.zip
current_received_zip_checked: mashos-api_7(81).zip
hash_matched_files: 3
```

一致確認したファイルは次の通り。

```text
mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701.py
mashos-api/ai/tests/test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op10_op11_20260702.py
mashos-api/ai/tests/R54_AHR_PostPMN23_DownstreamManualDecisionHold_EvidenceIntake_DMH_OP10_OP11_Result_20260702.md
```

## 3. 変更ファイル

```text
modified:
  mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701.py

new:
  mashos-api/ai/tests/test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op12_op13_20260702.py
  mashos-api/ai/tests/R54_AHR_PostPMN23_DownstreamManualDecisionHold_EvidenceIntake_DMH_OP12_OP13_Result_20260702.md
```

## 4. DMH-OP12 実装内容

DMH-OP12では、OP11のrating rows normalization materialを前提に、question need observation rowsをbody-freeに正規化する境界を追加した。

主な確認内容は次の通り。

```text
question_need_observation_row_count: 24 required
question_text_materialized_here: false
draft_question_text_materialized_here: false
question_trigger_logic_materialized_here: false
question_answer_storage_materialized_here: false
p8_implementation_spec_finalized_here: false
p8_start_allowed: false
body_free: true
next_required_step: DMH-OP13 rating-question consistency / blocker separation
```

このhelperが行うのは、body-freeなquestion need observation rowの受入・正規化である。質問文、draft質問文、trigger、storage、P8仕様、P8開始判断は作らない。

## 5. DMH-OP13 実装内容

DMH-OP13では、rating rowsとquestion observation rowsの整合を検査し、修正・安全・読感・実行blockerをP8 candidateへ逃がさないための分離guardを追加した。

主な確認内容は次の通り。

```text
rating_question_consistency_guard_passed: true required
p5_repair_required_cases_routed_to_p5_repair: true required
p4_repair_required_cases_routed_to_p4_repair: true required
safe_display_risk_cases_not_routed_to_p8: true required
operation_blocker_cases_not_routed_to_p8: true required
p8_start_allowed: false
p8_question_design_started_here: false
p8_question_implementation_started_here: false
next_required_step: DMH-OP14 disposal / purge receipt intake
```

このhelperは、P8候補を作る工程ではない。P8 materialに見えるものがあっても、rating未達・safe display risk・readfeel repair・execution blocker・inconclusive materialがある場合は、P8へ逃がさず、P5/P4修正またはoperation repairへ分ける。

## 6. body-free / no-promotion boundary

今回も次を維持した。

```text
api_changed: false
db_changed: false
rn_changed: false
runtime_changed: false
response_key_changed: false
public_response_top_level_key_added: false
body_full_packet_generation_run_here: false
actual_local_only_human_review_run_here: false
actual_operation_receipt_created_here: false
actual_sanitized_review_result_rows_created_here: false
actual_rating_rows_created_here: false
actual_question_need_observation_rows_created_by_real_operation_here: false
disposal_purge_run_here: false
postcr22_ex07_ex18_reentry_executed_here: false
p5_final_allowed: false
p6_start_allowed: false
p8_start_allowed: false
r52_actual_execution_confirmed: false
p7_complete: false
release_allowed: false
```

## 7. テスト結果

### 7.1 Target: DMH-OP12/OP13

```bash
cd /mnt/data/dmh_op12_op13_fresh/current/mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q tests/test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op12_op13_20260702.py
```

```text
45 passed in 16.10s
```

### 7.2 Immediate previous target: DMH-OP10/OP11

```bash
cd /mnt/data/dmh_op12_op13_fresh/current/mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q tests/test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op10_op11_20260702.py
```

```text
58 passed in 3.73s
```

### 7.3 Selected regression: PMN-OP22/OP23

通常pytest plugin autoloadでは終盤で環境側killが発生したため、pytest plugin autoloadを無効化して同一対象を再確認した。

```bash
cd /mnt/data/dmh_op12_op13_fresh/current/mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q tests/test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op22_op23_contract_20260630.py
```

```text
37 passed in 28.30s
```

### 7.4 compileall

```bash
cd /mnt/data/dmh_op12_op13_fresh/current/mashos-api/ai
python3 -m compileall -q services/ai_inference tests
```

```text
passed
```

## 8. 主張しないこと

今回、次は主張しない。

```text
full_backend_suite_green_claimed: false
rn_contract_green_claimed: false
rn_real_device_modal_verified_claimed: false
actual_human_review_evidence_complete_claimed: false
actual_body_full_packet_generation_claimed: false
actual_local_only_human_review_execution_claimed: false
actual_question_need_observation_rows_from_real_operation_claimed: false
p5_finalization_claimed: false
p6_start_claimed: false
p8_start_claimed: false
p8_question_design_claimed: false
p8_question_implementation_claimed: false
r52_actual_execution_claimed: false
p7_complete_claimed: false
release_allowed_claimed: false
```

## 9. 次工程

次に進める場合の工程は次である。

```text
DMH-OP14: disposal / purge receipt intake
```

ただし、OP14でもbody-full packet lifecycleのreceipt boundaryを扱うだけであり、P5/P6/P8/R52/P7 complete/releaseへ自動昇格しない。
