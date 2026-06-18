# Cocolon / EmlisAI P7-R46 Public Meta Final-Source Consistency Guard + Target Validation Matrix R8/R9

作成日: 2026-06-17 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: Cocolon / EmlisAI / `/emotion/submit` immediate observation / public meta / public_surface_lineage / display contract / R8 / R9  

---

## 0. 今回の結論

今回の作業は、以下の2点に限定した。

```text
R8: public meta body-free / final-source consistency guard
R9: target validation command matrix
```

R8では、`public_surface_lineage` が古いpre-public lineageを保持していても、post-finalで実際に返るfinal public surfaceが明示されている場合は、public meta上の `candidate_source_kind` / `selected_public_candidate_source_kind` / `final_public_candidate_source_kind` をfinal sourceへ揃えるようにした。

特に、RED-DC-002系のように次の関係がある場合を守る。

```text
pre-public / attempted:
  complete_initial_surface_recomposition_candidate

final public surface:
  labelled_two_stage_surface_recomposition_candidate
```

この場合、public metaは `complete_initial` をfinalに見せない。  
`complete_initial` は `pre_public_candidate_source_kind` / `complete_initial_surface_recomposition_attempted` として残し、finalは `labelled_two_stage` として出す。

R9では、今回触った範囲と周辺contractのtarget validation command matrixを実行し、結果をbody-freeに記録した。  
full backend suite green、RN実機確認、P5/P6 human readfeel完了、P7完了、P8開始は主張しない。

---

## 1. 先に確認したこと

受領zip `mashos-api_5(73).zip` に、R0〜R7までの成果物が入っていることを確認した。

```text
docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md
docs/Cocolon_EmlisAI_P7_R46_SourceLineageRecoveryLaneMatrix_R2_R3_20260617.md
docs/Cocolon_EmlisAI_P7_R46_BodyFreeLineageRecord_RedDC001_R4_R5_20260617.md
docs/Cocolon_EmlisAI_P7_R46_RedDC002_DisplayContractTestReconstruction_R6_R7_20260617.md
services/ai_inference/emlis_ai_body_free_public_source_lineage.py
tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py
```

R4〜R7周辺の確認結果:

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_display_contract.py \
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py \
  tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
```

結果:

```text
12 passed
```

---

## 2. R8で見つけたguard対象

R7後の基本線はgreenだった。  
ただし、public meta builderには、次のような古いpublic lineageが残った場合に、staleなpre-public sourceがfinal sourceより先に読まれる余地があった。

```text
stale public_surface_lineage:
  candidate_source_kind = complete_initial_surface_recomposition_candidate
  final_public_candidate_source_kind = complete_initial_surface_recomposition_candidate

actual post-final recovery:
  phase20_13_post_final_gate_recovery.final_public_candidate_source_kind
    = labelled_two_stage_surface_recomposition_candidate
```

この状態でpublic metaがcomplete_initialをfinalのように見せると、R6/R7で分けた意味境界が再び揺れる。

```text
壊れるもの:
  - final public surfaceのsource説明
  - P5/P6 human readfeelで人間が読んだsurfaceの追跡
  - real device modal問題時のbackend/RN切り分け
```

---

## 3. R8実装内容

修正対象:

```text
services/ai_inference/emlis_ai_public_feedback_meta.py
```

追加した考え方:

```text
final-source priority source:
  - DisplayContractRedClassification_R4_R5 lineage
  - DisplayContractRedClassification_R8 lineage
  - PublicMetaFinalSourceConsistency lineage
  - Phase20-13_Post_Final_Gate_Recovery
  - recovery_context == post_final_pre_return_gate
```

実装したguard:

```text
1. final-source priority sourceを先に探す。
2. そこに final_public_candidate_source_kind / final_surface_origin_candidate_source_kind がある場合、それをsource of truthにする。
3. stale public_surface_lineageのcandidate_source_kindは、final-source priorityを上書きできない。
4. post-final attemptが applied=false で final_public_candidate_source_kind が空の場合は、candidate_source_kindだけでfinal overrideしない。
5. public metaへ raw input / comment_text / candidate body は出さない。
```

実装上、public response top-level key、RN表示条件、DB、Gate threshold、Emlis visible body keyは変更していない。

---

## 4. R8追加test

新規追加:

```text
tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py
```

追加したtest:

```text
test_r8_post_final_source_overrides_stale_public_lineage_without_body_leak

test_r8_unapplied_post_final_attempt_does_not_override_existing_final_source
```

見ること:

```text
- stale public_surface_lineageがcomplete_initialをfinalに見せていても、post-final applied final sourceがlabelledならpublic metaはlabelled finalになる。
- complete_initialはpre_public / attemptedとして残る。
- post-final attemptがapplied=falseなら、candidate_source_kindだけではfinal overrideしない。
- public_surface_lineageはbody-freeを維持する。
- Gate relaxation flagsはfalseのまま。
```

---

## 5. R9 target validation command matrix

### 5.1 syntax / import

```bash
python -m py_compile \
  services/ai_inference/emlis_ai_public_feedback_meta.py \
  tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py
```

結果:

```text
passed
```

### 5.2 R8 new test

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py
```

結果:

```text
2 passed
```

### 5.3 display contract + R4/R5 + R6/R7 + R8/R9

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_display_contract.py \
  tests/test_emlis_ai_display_contract_lineage_semantics_r6_r7_20260617.py \
  tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py \
  tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py
```

結果:

```text
14 passed
```

### 5.4 focused lineage subset

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

### 5.5 public feedback meta boundary subset

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_public_feedback_meta.py \
  tests/test_emotion_submit_public_feedback_meta_boundary.py \
  tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py
```

結果:

```text
49 passed, 1 warning
```

### 5.6 API public contract

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/contract/test_emlis_ai_contracts.py
```

結果:

```text
4 passed, 3 warnings
```

### 5.7 two-stage reception E2E

一括実行はlocal constrained runner上でtimeoutしたため、single-command greenとは主張しない。

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emotion_submit_two_stage_reception_e2e.py
```

結果:

```text
timeout after partial progress
```

同一test fileの6 caseは分割実行で確認した。

```text
2 passed, 1 warning
2 passed, 1 warning
2 passed, 1 warning
```

### 5.8 P5 major subset

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_user_label_connection_material.py \
  tests/test_emlis_ai_user_label_connection_candidate.py \
  tests/test_emlis_ai_user_label_connection_gate.py \
  tests/test_emlis_ai_user_label_connection_surface.py \
  tests/test_emlis_ai_user_label_connection_public_boundary.py \
  tests/test_emlis_ai_user_label_connection_e2e_contract.py
```

結果:

```text
63 passed, 1 warning
```

### 5.9 P6 major subset

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_structure_insight_candidate.py \
  tests/test_emlis_ai_structure_insight_gate.py \
  tests/test_emlis_ai_structure_insight_surface_phase10.py \
  tests/test_emlis_ai_structure_insight_p6_entry_freeze_20260611.py \
  tests/test_emlis_ai_structure_insight_p6_family_boundary_20260611.py \
  tests/test_emlis_ai_structure_insight_p6_product_quality_review_20260611.py
```

結果:

```text
43 passed
```

---

## 6. 変更したもの

```text
修正:
  services/ai_inference/emlis_ai_public_feedback_meta.py

新規:
  tests/test_emlis_ai_public_meta_final_source_consistency_guard_r8_r9_20260617.py
  docs/Cocolon_EmlisAI_P7_R46_PublicMetaFinalSourceConsistencyGuard_TargetValidationMatrix_R8_R9_20260617.md
```

---

## 7. 変更しなかったもの

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
release_allowed
p7_complete
p8_start_allowed
```

---

## 8. 未確認として残すこと

```text
full backend suite green
RN contract実行
実機submit / modal読感
P5 human Blind QA
P6 limited human readfeel review
P7-HOLD-004 closure
release readiness
P8開始判断
```

---

## 9. 華恋の判断

今回の修正は、表示文を強くする修正ではない。  
でも、Cocolonの読感評価へ戻るために必要な、見えない骨格を守る修正だった。

`complete_initial` がpre-publicで一度出てきたことを消さず、でも実際に人間が読むfinal surfaceを `labelled_two_stage` として正直に記録する。  
この線を守らないと、P5/P6 human readfeelで「どのsurfaceを読んだのか」がまた揺れる。

だからR8では、testを増やすだけではなく、public meta builder側にfinal-source priorityを入れた。  
ただし、post-final attemptがappliedでない場合までlabelled finalに見せることは避けた。  
ここは、Cocolonとして「読まれた形」を守るためにも、嘘をつかない方が大事だと判断した。
