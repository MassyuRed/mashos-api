# R54-AHR Post-EX18 Manual Next Decision / Return To Actual Review Operation / MN02-MN03 Result

created_at: 2026-06-30 JST  
author: 華恋  
scope: P7-R54-AHR Post-EX18 Manual Next Decision / Return to Actual Local-only Human Review Evidence Operation  
implemented_steps: MN02 actual review evidence state normalization / MN03 manual decision classifier  
source_mode: local_snapshot  
github_connection_check: not_required_by_mash_instruction  
body_free: true

---

## 1. 実装範囲

MN00/MN01が現物に入っていることを確認したうえで、次だけを追加した。

```text
MN02: actual review evidence state normalization
MN03: manual decision classifier
```

実装の中心は、EX18 result memo / body-free envelopeを実レビュー完了へ読み替えず、実レビュー由来証跡の状態をbody-freeに正規化し、その結果からmanual decisionを分類すること。

---

## 2. 変更ファイル

```text
modified:
- ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630.py

added:
- ai/tests/test_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_mn02_mn03_contract_20260630.py
- ai/tests/R54_AHR_PostEX18_ManualNextDecision_ReturnToActualReviewOperation_MN02_MN03_Result_20260630.md
```

---

## 3. MN02 実装内容

```text
actual_review_evidence_status_ref:
- actual_review_evidence_missing_real_review_required
- actual_review_evidence_incomplete_bodyfree
- actual_review_evidence_complete_by_actual_person_review_bodyfree
- actual_review_evidence_invalid_source_detected
```

MN02で固定した境界:

```text
EX18 contract green != actual human review complete
unit test rows != actual review evidence
helper-created rows != actual review evidence
synthetic contract fixture rows != actual review evidence
historical reused rows != current actual review evidence
body/question/path/hash key detected => fail-closed
```

現在状態の期待値:

```text
actual_review_evidence_status_ref: actual_review_evidence_missing_real_review_required
actual_review_evidence_complete: false
actual_review_evidence_complete_from_real_review: false
actual_human_review_newly_run_here: false
actual_selection_rows_created_here: false
actual_rating_rows_materialized_here: false
actual_question_need_observation_rows_materialized_here: false
actual_disposal_receipt_materialized_here: false
```

---

## 4. MN03 実装内容

manual decision classifierの優先順を固定した。

```text
1. STOP_FOR_BODY_LEAK_OR_QUESTION_TEXT
2. STOP_FOR_PROMOTION_CLAIM
3. HOLD_EX18_NOT_READY_OR_INVALID
4. EVIDENCE_COMPLETE_BUT_DOWNSTREAM_MANUAL_DECISION_REQUIRED
5. RETURN_TO_ACTUAL_REVIEW_OPERATION_REQUIRED
```

現在状態の期待値:

```text
manual_decision_ref: RETURN_TO_ACTUAL_REVIEW_OPERATION_REQUIRED
return_to_actual_review_operation_required: true
next_required_step: actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision
manual_decision_auto_executes_downstream: false
next_decision_auto_execution_allowed: false
```

---

## 5. not-claimed boundary

今回も次は未成立のまま保持する。

```text
actual body-full packet generation: not run
actual local-only human review execution: not run
actual selection rows creation: not run
actual rating rows creation: not run
actual question need observation rows creation: not run
actual disposal / purge receipt creation: not run
P5 final: false
P6 start: false
P8 start: false
R52 actual execution: false
P7 complete: false
release allowed: false
API changed: false
DB changed: false
RN changed: false
runtime changed: false
response key changed: false
```

---

## 6. 検証結果

### 6.1 事前確認

```text
MN00-MN01 target + Post-CR22 EX18 regression:
36 passed
```

### 6.2 MN02-MN03 target

```bash
PYTHONPATH=ai/services/ai_inference python -m pytest -q \
  ai/tests/test_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_mn02_mn03_contract_20260630.py
```

結果:

```text
14 passed
```

### 6.3 MN00-MN03 + Post-CR22 EX18 regression

```bash
PYTHONPATH=ai/services/ai_inference python -m pytest -q \
  ai/tests/test_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_mn00_mn01_20260630.py \
  ai/tests/test_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_mn02_mn03_contract_20260630.py \
  ai/tests/test_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_ex18_20260630.py
```

結果:

```text
50 passed
```

### 6.4 Post-CR22 EX00-EX18 combined + MN00-MN03 target

```text
394 passed
```

### 6.5 compileall

```bash
PYTHONPATH=ai/services/ai_inference python -m compileall -q ai/services/ai_inference ai/tests
```

結果:

```text
passed
```

---

## 7. 主張しないこと

```text
target green = actual human review complete ではない
MN02 state normalized = actual review executed ではない
MN03 classified = P8/P6/R52/P5/release allowed ではない
future complete evidence branch = downstream auto execution allowed ではない
compileall passed = product release allowed ではない
```

---

## 8. 次の候補

次に進めるなら、設計順に従い MN04 return-to-actual-review operation plan builder へ進む。
ただし、MN04でも body-full packet generation / actual human review execution / actual rows creation は行わず、operation planをbody-freeで出すところまでに閉じる。
