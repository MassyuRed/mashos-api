# Cocolon / EmlisAI P7-R46 R12/R13 実装結果: real device submit / modal読感 checklist + P7 hold / release / P8 closed validation

作成日: 2026-06-17 JST  
作成者: 華恋  
対象: Cocolon / EmlisAI / P7-R46 / P5-P6 return / real device modal review / release closed validation  
作業範囲: R12 / R13  
GitHub接続確認: Mash指定により不要。未実施。  
RN変更: なし。  
API route / request key / public response top-level key変更: なし。  
DB変更: なし。  
Gate閾値変更: なし。  
Emlis本文runtime変更: なし。  
実機review実施: なし。  
release_allowed / p7_complete / p8_start_allowed: false維持。  

---

## 0. 結論

R12/R13では、実機submit / modal読感を確認済みにするのではなく、確認するための body-free checklist と、P7 / release / P8 を閉じたままにする validation material を追加した。

今回追加した実ファイルは次。

```text
services/ai_inference/emlis_ai_p7_r46_real_device_modal_review_closed_validation.py
tests/test_emlis_ai_p7_r46_real_device_modal_review_closed_validation_r12_r13_20260617.py
docs/Cocolon_EmlisAI_P7_R46_RealDeviceModalReviewChecklist_ClosedValidation_R12_R13_20260617.md
```

今回修正した既存ファイルはない。

---

## 1. ここまでの受領実装確認

受領zip `mashos-api_7(60).zip` に、R0〜R11の成果物が入っていることを確認した。

```text
R0/R1:
  docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md

R2/R3:
  docs/Cocolon_EmlisAI_P7_R46_SourceLineageRecoveryLaneMatrix_R2_R3_20260617.md

R4/R5:
  docs/Cocolon_EmlisAI_P7_R46_BodyFreeLineageRecord_RedDC001_R4_R5_20260617.md
  services/ai_inference/emlis_ai_body_free_public_source_lineage.py
  tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py

R6/R7:
  docs/Cocolon_EmlisAI_P7_R46_RedDC002_DisplayContractTestReconstruction_R6_R7_20260617.md
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py

R8/R9:
  docs/Cocolon_EmlisAI_P7_R46_PublicMetaFinalSourceConsistencyGuard_TargetValidationMatrix_R8_R9_20260617.md
  services/ai_inference/emlis_ai_public_feedback_meta.py
  tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py

R10/R11:
  docs/Cocolon_EmlisAI_P7_R46_P5P6HumanReadfeelHandoffMaterial_R10_R11_20260617.md
  services/ai_inference/emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material.py
  tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py
```

R4〜R11 combinedは、作業前確認で `20 passed`。

---

## 2. R12: real device submit / modal読感 checklist設計

追加module:

```text
services/ai_inference/emlis_ai_p7_r46_real_device_modal_review_closed_validation.py
```

主なbuilder:

```text
build_real_device_submit_modal_readfeel_checklist
assert_real_device_submit_modal_readfeel_checklist_contract
```

R12で固定したこと:

```text
- default result は NOT_RUN。
- 実機manual reviewが未実施なら real_device_modal_review_confirmed=false。
- automated greenだけでは manual real device review を閉じない。
- HOLD-RD-001 / P7-HOLD-003 を維持する。
- review用payload本文はmaterial化しない。
- RN / API / DB / Gate / Emlis本文runtime は変更しない。
```

checklistで扱う確認対象は、body-freeなstatus / identifierのみ。

```text
modal contract:
  submit_modal_opened
  title_emlis_observation_preserved
  visible_payload_source_confirmed
  passed_non_empty_only_confirmed
  non_passed_hidden_confirmed
  public_top_level_shape_preserved

readfeel:
  phone_readability_reviewed
  length_pressure_reviewed
  line_break_reviewed
  section_weight_reviewed
  p5_history_line_creepy_absence_reviewed
  p6_structure_insight_overread_absence_reviewed
  wants_more_input_reviewed
```

manual reviewが将来PASSとして記録されても、このmodule単体ではrelease / P7 complete / P8 startへ昇格しない。

---

## 3. R13: P7 hold / release / P8 closed validation

主なbuilder:

```text
build_p7_hold_release_p8_closed_validation
assert_p7_hold_release_p8_closed_validation_contract
build_real_device_and_closed_validation_summary
assert_real_device_and_closed_validation_summary_contract
```

R13で固定したこと:

```text
release_allowed=false
p7_complete=false
p8_start_allowed=false
hold004_close_allowed=false
full_backend_suite_green_confirmed=false
p5_human_blind_qa_confirmed=false
p6_human_readfeel_confirmed=false
```

P5/P6は、R10/R11のhandoff materialにより「ready」にはできる。  
ただし、人間reviewが未実施のまま `confirmed=true` にはしない。

実機modalは、R12 checklistにより「checklist_ready」にはできる。  
ただし、未実施なら `result=NOT_RUN` / `confirmed=false` のまま残す。

R13で未解決として維持する主なHOLD:

```text
P7-HOLD-001 / HOLD-P5-001: P5 human Blind QA未実施
P7-HOLD-002 / HOLD-P6-001: P6 limited human readfeel未実施
P7-HOLD-003 / HOLD-RD-001: real device submit / modal読感未実施
P7-HOLD-004 / HOLD-DC-005: full backend suite / closure未確認
```

---

## 4. body-free境界

今回のR12/R13 materialへ入れないもの:

```text
- raw input
- memo / memo_action
- comment_text
- candidate body
- surface body
- reviewer free text
- terminal output
- traceback
```

入力mappingにこれらのpayload keyが入った場合、builderが `ValueError` を返すtestを追加した。

---

## 5. validation結果

R12/R13新規test:

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_p7_r46_real_device_modal_review_closed_validation_r12_r13_20260617.py
```

結果:

```text
6 passed
```

R4〜R13 combined:

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py \
  tests/test_emlis_ai_display_contract.py \
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py \
  tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py \
  tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py \
  tests/test_emlis_ai_p7_r46_real_device_modal_review_closed_validation_r12_r13_20260617.py
```

結果:

```text
26 passed
```

syntax / import:

```text
passed
```

P5 major subset:

```text
63 passed, 1 warning
```

P6 major subset:

```text
43 passed
```

API public contract:

```text
4 passed, 3 warnings
```

two-stage reception E2E:

```text
一括実行はlocal constrained runner上でtimeout。
一部node指定の分割実行もtimeoutしたため、今回のR12/R13ではtwo-stage reception E2E greenは主張しない。
```


---

## 6. 変更しなかったこと

```text
RN production UI
RN表示タイトル
RN表示条件
/emotion/submit route
request key
public response top-level key
DB schema
DB write path
Gate threshold
Emlis visible body key
fixed commentText
case専用surface
case専用mode
public meta builder
reply runtime
actual real device review packet
actual human review packet
release_allowed
p7_complete
p8_start_allowed
hold004_close_allowed
```

---

## 7. 未確認として残したこと

```text
full backend suite green
RN contract実行
実機submit / modal読感
P5 human Blind QA実施
P6 limited human readfeel review実施
P7-HOLD-004 / HOLD-DC-005 closure
release readiness
P8開始判断
```

---

## 8. 華恋の判断

今回のR12/R13で大事なのは、実機確認を進める入口を作りつつ、未実施のものを確認済みにしないこと。  
RN contract green、backend subset green、display contract greenは、modalで人間が読んだ時の重さ・怖さ・また残したさを証明しない。

そのため、今回の実装では実機reviewをPASS扱いにせず、defaultを `NOT_RUN` にした。  
Cocolonとしては、ここを曖昧にすると「表示できる」と「もう一回残したい」が混ざる。  
今回のR12/R13は、その混ざりを防ぐための境界として入れている。
