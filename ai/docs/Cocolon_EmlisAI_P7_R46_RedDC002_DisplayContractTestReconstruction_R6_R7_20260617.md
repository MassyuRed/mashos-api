# Cocolon / EmlisAI P7-R46 RED-DC-002 分類・display contract test再構成 R6/R7 実装メモ

作成日: 2026-06-17 JST  
作成者: 華恋  
対象: `mashos-api/ai` / EmlisAI / display contract / source lineage / recovery lane  
作業範囲: R6 / R7  
RN変更: なし  
API route / request key / public response top-level key変更: なし  
DB変更: なし  
Gate閾値変更: なし  
Emlis visible body runtime変更: なし  
production code変更: なし  

---

## 0. 結論

R6/R7では、残っていたRED-DC-002を次のように分類して扱った。

```text
RED-DC-002:
  type: test expectation stale + display contract semantic drift
  runtime final surface: labelled_two_stage_surface_recomposition_candidate
  pre-public attempted source: complete_initial_surface_recomposition_candidate
  complete_initial final used: false
  labelled_two_stage final used: true
  public lineage final source consistency: passed
  body leak: not observed in R6/R7 target scope
  Gate relaxation: not observed in R6/R7 target scope
```

今回の修正は、`complete_initial` をfinalとして見せかける修正ではない。  
`complete_initial` はpre-public / attemptedとして保持し、実際に返るfinal public surfaceは `labelled_two_stage` としてtest contractを再構成した。

---

## 1. ここまでの実装確認

受領zipには、R0〜R5までの成果物が入っていることを確認した。

```text
mashos-api/ai/docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md
mashos-api/ai/docs/Cocolon_EmlisAI_P7_R46_SourceLineageRecoveryLaneMatrix_R2_R3_20260617.md
mashos-api/ai/docs/Cocolon_EmlisAI_P7_R46_BodyFreeLineageRecord_RedDC001_R4_R5_20260617.md
mashos-api/ai/services/ai_inference/emlis_ai_body_free_public_source_lineage.py
mashos-api/ai/tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
```

また、R2/R3/R4/R5で追加した以下のlineage fieldが現行production meta / public metaへ接続されていることを確認した。

```text
root_candidate_source_kind
recovery_input_candidate_source_kind
selected_public_candidate_source_kind
pre_public_candidate_source_kind
final_public_candidate_source_kind
lineage_consistency_passed
complete_initial_surface_recomposition_attempted
complete_initial_surface_recomposition_final_used
labelled_two_stage_surface_recomposition_final_used
```

---

## 2. R6: RED-DC-002 pre-connection recovery lane mismatch分類

### 2.1 受領時点の状態

R6開始時点のdisplay contractは次だった。

```text
4 passed / 1 failed
```

残赤は以下のみ。

```text
expected:
  candidate["composer_model"] == "complete_initial_surface_recomposition_v1"

actual:
  candidate["composer_model"] == "labelled_two_stage_surface_recomposition_v1"
```

### 2.2 R6で確認したactual lineage

pre-connection / source unavailable系ケースでは、runtime final candidateは次だった。

```text
candidate.composer_model:
  labelled_two_stage_surface_recomposition_v1

composer_meta.candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

composer_meta.root_candidate_source_kind:
  unavailable

composer_meta.recovery_input_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

composer_meta.pre_public_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

composer_meta.selected_public_candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

composer_meta.final_public_candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate
```

complete initial summaryは次の扱いだった。

```text
attempted: true
candidate_generated: true
applied: false
candidate_adopted_after_existing_gates: false
passed_by_all_existing_gates: false
existing_gate_chain.visible_surface_acceptance_gate_passed: false
existing_gate_chain.blocked_reasons includes:
  visible_surface_acceptance_gate_failed
```

public lineageは次の扱いだった。

```text
candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

pre_public_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

final_public_candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

lineage_consistency_passed:
  true

complete_initial_surface_recomposition_attempted:
  true

complete_initial_surface_recomposition_final_used:
  false

labelled_two_stage_surface_recomposition_final_used:
  true
```

### 2.3 R6分類

RED-DC-002は、production final candidateを `complete_initial` に戻すruntime redではなく、test contract側がfinal candidateとpre-public attempted laneを混同していた赤として分類する。

```text
primary:
  test_expectation_stale

secondary:
  display_contract_semantic_drift

closed as primary runtime lane regression:
  false

closed as body leak:
  false

closed as Gate relaxation:
  false
```

---

## 3. R7: display contract test再構成

### 3.1 修正対象

```text
tests/test_emlis_ai_display_contract.py
tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py
```

### 3.2 再構成したassert

既存test fileをpublic display contractの中心として残し、pre-connection recoveryのsource assertionを意味別に分けた。

```text
final candidate assertion:
  candidate["composer_model"] == "labelled_two_stage_surface_recomposition_v1"
  composer_meta["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
  composer_meta["final_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"

pre-public attempted assertion:
  composer_meta["recovery_input_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
  composer_meta["pre_public_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
  complete_initial_summary["attempted"] is True
  complete_initial_summary["applied"] is False
  complete_initial_summary["existing_gate_chain"]["blocked_reasons"] includes "visible_surface_acceptance_gate_failed"

public lineage consistency assertion:
  public_lineage["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
  public_lineage["final_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
  public_lineage["pre_public_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
  public_lineage["lineage_consistency_passed"] is True
  public_lineage["complete_initial_surface_recomposition_final_used"] is False
  public_lineage["labelled_two_stage_surface_recomposition_final_used"] is True

body-free / Gate boundary:
  raw_input_included is False
  comment_text_body_included is False
  candidate_body_included is False
  Gate relaxation flags remain false
```

### 3.3 追加したsemantic test

`tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py` を追加した。  
目的は、display contract本体のe2eに閉じ込めすぎず、public meta builder単位で次を固定すること。

```text
1. pre-connection complete_initial attempt does not override labelled final
2. phase20_5 pre-public source is kept separate from post-final source
3. gate recovery material surface stays forbidden and body-free
```

このtestは、raw input / comment_text / candidate bodyをfixtureとして持たない。  
識別子・boolean・body-free boundaryだけを確認する。

### 3.4 変更しなかったこと

```text
production code
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
```

---

## 4. validation

### 4.1 syntax / import

```bash
python -m py_compile \
  tests/test_emlis_ai_display_contract.py \
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py \
  services/ai_inference/emlis_ai_body_free_public_source_lineage.py \
  services/ai_inference/emlis_ai_public_feedback_meta.py \
  services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py
```

結果:

```text
passed
```

### 4.2 display contract + R6/R7 semantic test

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_display_contract.py \
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py
```

結果:

```text
8 passed
```

### 4.3 R4/R5 + display contract + R6/R7 semantic test

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py \
  tests/test_emlis_ai_display_contract.py \
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py
```

結果:

```text
12 passed
```

### 4.4 focused subset

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_labelled_two_stage_surface_recomposition_p6.py \
  tests/test_emlis_ai_public_meta_product_quality_lineage_p8.py \
  tests/test_emlis_ai_gate_recovery_public_candidate_builder_p5.py
```

結果:

```text
16 passed
```

### 4.5 API public contract

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/contract/test_emlis_ai_contracts.py
```

結果:

```text
4 passed, 3 warnings
```

### 4.6 two-stage reception E2E

一括実行はlocal constrained runner上でtimeoutし、single-command greenとは主張しない。  
同一test fileの6 caseは分割実行で確認した。

```text
2 passed, 1 warning
2 passed, 1 warning
2 passed, 1 warning
```

---

## 5. 確認済み

```text
- R0/R1/R2/R3/R4/R5の成果物は受領zipに入っていた。
- R6開始時点で残赤はRED-DC-002のみだった。
- RED-DC-002はinput_feedback absentではない。
- RED-DC-002はcomment_text emptyではない。
- RED-DC-002は、観測範囲ではbody leakではない。
- RED-DC-002は、観測範囲ではGate relaxationではない。
- complete_initialはattempted / pre-publicとして保持されている。
- complete_initialはvisible_surface_acceptance_gate_failedによりfinalではない。
- final public surfaceはlabelled_two_stageである。
- public lineageはfinal labelled sourceと一致している。
- display contractは5 passedになった。
```

---

## 6. 未確認

```text
- full backend suite green
- P5 human Blind QA
- P6 limited human readfeel review
- real device submit / modal読感確認
- release_allowed / p7_complete / p8_start_allowed の変更可否
```

---

## 7. 書かれていない

```text
- R6/R7でproduction runtimeを変更する指示
- R6/R7でRN UIを変更する指示
- R6/R7でAPI key / route / DBを変更する指示
- R6/R7でGate thresholdを緩める指示
- R6/R7でcomplete_initialをfinalとして偽装する指示
- R6/R7でP5/P6 human readfeel完了扱いにする指示
- R6/R7でP7完了 / P8開始へ進む指示
```

---

## 8. 華恋の意見

今回のRED-DC-002は、表示できているから無視してよい赤ではなかった。  
ただし、runtimeをcomplete_initialへ戻す赤でもなかった。

大事だったのは、`complete_initial` を失敗扱いで捨てることではなく、**pre-publicで一度作られたがfinalではない候補**として残し、実際に人間が読むsurfaceを `labelled_two_stage` として正直に記録することだった。

ここをtest期待だけで雑に直すと、P5/P6読感へ戻った時に、どのsurfaceを人間が読んだのかが曖昧になる。  
今回は、testをfinal / pre-public / body-free lineageに分けたので、次にP5/P6 human readfeelへ戻るための評価材料が少し安定した。

この先は、R8でpublic meta body-free / final-source consistency guardを閉じ、R9でvalidation matrixを固定してから、P5/P6 review materialへ戻るのが安全だと思う。
