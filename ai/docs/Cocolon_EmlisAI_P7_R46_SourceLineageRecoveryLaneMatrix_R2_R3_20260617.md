# Cocolon / EmlisAI P7-R46 Display Contract Red Classification R2/R3 実装結果

作成日: 2026-06-17 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: `mashos-api/ai` / EmlisAI display contract / source lineage / recovery lane decision matrix  
範囲: R2 / R3  
GitHub接続確認: Mash指定により不要。未実施。  

---

## 0. 結論

R0/R1成果物が現行受領zipに入っていることを確認した上で、R2/R3まで進めた。

今回の実装は、display contract赤を無理にgreen化する作業ではない。  
R2/R3として、source lineage語彙とrecovery lane decision matrixをruntime meta / public meta上でbody-freeに固定した。

今回の到達点は次。

```text
R0/R1成果物確認:
  docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md が現行zip内に存在。

R2:
  root / recovery_input / selected / pre_public / final のsource lineage語彙を実装へ追加。
  original_candidate_source_kind は root_candidate_source_kind の既存互換aliasとして扱う。

R3:
  pre-public recovery と post-final pre-return recovery をpublic lineage上で分離。
  complete_initial attempted / pre_public と labelled final を混同しないようにした。
```

---

## 1. 変更ファイル

### 修正

```text
services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py
services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py
services/ai_inference/emlis_ai_public_feedback_meta.py
services/ai_inference/emlis_ai_reply_service.py
```

### 新規

```text
docs/Cocolon_EmlisAI_P7_R46_SourceLineageRecoveryLaneMatrix_R2_R3_20260617.md
```

---

## 2. R0/R1確認

現行受領zip内に、前回成果物が入っていることを確認した。

```text
docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md
```

また、現行display contractを再実行し、R0/R1の赤再現と矛盾しないことを確認した。

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/test_emlis_ai_display_contract.py
```

R2/R3着手前の再現状態:

```text
3 passed / 2 failed

RED-DC-001:
  expected: original_candidate_source_kind == ai_generated
  actual:   labelled_two_stage_surface_recomposition_candidate

RED-DC-002:
  expected: composer_model == complete_initial_surface_recomposition_v1
  actual:   labelled_two_stage_surface_recomposition_v1
```

---

## 3. R2: source lineage語彙と意味境界の固定

### 3.1 固定した語彙

次のbody-free source lineage語彙を追加・伝播するようにした。

```text
root_candidate_source_kind:
  最初のcandidate source。既存 original_candidate_source_kind の意味境界として扱う。

recovery_input_candidate_source_kind:
  今回のrecovery passへ渡されたcandidate source。

selected_public_candidate_source_kind:
  recovery passで選ばれたpublic candidate source。

pre_public_candidate_source_kind:
  pre-public boundaryで一度採用されたcandidate source。

final_public_candidate_source_kind:
  final pre-return後、実際に返るpublic candidate source。
```

### 3.2 既存互換方針

`original_candidate_source_kind` は削除せず、root sourceのaliasとして維持した。

理由:

```text
- 既存display contractがこのfieldを見ている。
- RED-DC-001の本質は、root sourceがnested recoveryで上書きされていたこと。
- rootを消すと、unsupported / ai_generated 由来candidateからのrecoveryが説明できなくなる。
```

### 3.3 実装内容

`emlis_ai_gate_recovery_public_candidate_builder.py` では、body-free lineage record builderを追加した。

```text
build_body_free_public_source_lineage_record
```

このrecordは、source kind / recovery context / boolean flagだけを持ち、本文bodyは持たない。

本文禁止境界:

```text
raw_input_included=false
comment_text_body_included=false
candidate_body_included=false
```

Gate緩和禁止境界:

```text
display_gate_relaxed=false
runtime_surface_gate_relaxed=false
visible_surface_gate_relaxed=false
grounding_gate_relaxed=false
template_gate_relaxed=false
safety_gate_relaxed=false
```

---

## 4. R3: recovery lane decision matrixの固定

### 4.1 固定した判定

今回の実装では、次を分けた。

```text
pre-public recovery:
  complete_initial が一度public candidateとして採用候補になる可能性がある。

post-final pre-return recovery:
  complete_initial がvisible gate等で落ちた後、two-stage required が残るなら labelled two-stage へ進む可能性がある。

final public surface:
  実際に reply.comment_text として返るcandidate source。
```

### 4.2 RED-DC-002の扱い

RED-DC-002では、現行runtime上、final candidateは labelled two-stage である。

今回、public meta上で次のように分けた。

```text
root_candidate_source_kind:
  source_unavailable

recovery_input_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

pre_public_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

final_public_candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

complete_initial_surface_recomposition_attempted:
  true

complete_initial_surface_recomposition_final_used:
  false

labelled_two_stage_surface_recomposition_final_used:
  true
```

これにより、complete_initialを「なかったこと」にせず、同時にfinal sourceをcomplete_initialとして偽装しない形にした。

---

## 5. RED-DC-001の状態

R2実装により、RED-DC-001は解消した。

実行結果:

```text
tests/test_emlis_ai_display_contract.py
  4 passed / 1 failed
```

RED-DC-001は、既存display contract内で通過するようになった。

確認された意味:

```text
candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

original_candidate_source_kind:
  ai_generated

root_candidate_source_kind:
  ai_generated

final_public_candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate
```

つまり、root sourceは `ai_generated` として保持し、final sourceは `labelled_two_stage_surface_recomposition_candidate` として分けられるようになった。

---

## 6. RED-DC-002の状態

RED-DC-002は、既存display contract上はまだ残る。

残っている赤:

```text
tests/test_emlis_ai_display_contract.py::test_step10_e2e_pre_connection_recovery_exposes_safe_surface_without_body_leak

expected:
  candidate["composer_model"] == "complete_initial_surface_recomposition_v1"

actual:
  "labelled_two_stage_surface_recomposition_v1"
```

この赤を今回のR2/R3でtest期待値変更して消さなかった。

理由:

```text
- final candidateがlabelledになること自体は、post-final pre-return recoveryのlaneとして説明できる。
- complete_initialはpre-public / attemptedとして保持するべきで、finalとして偽装するべきではない。
- 既存test期待値を変更するのはR7のdisplay contract test再構成範囲。
- R2/R3でRED-DC-002をgreen化するためにtestだけを書き換えると、R2/R3の意味固定とR7のtest再構成が混ざる。
```

ただし、public lineage上の矛盾は修正した。

修正後のbody-free public lineage:

```text
candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

root_candidate_source_kind:
  source_unavailable

recovery_input_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

pre_public_candidate_source_kind:
  complete_initial_surface_recomposition_candidate

final_public_candidate_source_kind:
  labelled_two_stage_surface_recomposition_candidate

complete_initial_surface_recomposition_attempted:
  true

complete_initial_surface_recomposition_used:
  false

complete_initial_surface_recomposition_final_used:
  false

labelled_two_stage_surface_recomposition_used:
  true

labelled_two_stage_surface_recomposition_final_used:
  true

lineage_consistency_passed:
  true
```

---

## 7. 変更しなかった範囲

今回、以下は変更していない。

```text
RN production UI
RN表示タイトル
RN表示条件
/emotion/submit route
request key
public response top-level key
DB schema
DB write path
subscription entitlement判定
Gate threshold
Emlis visible body key
fixed commentText
case専用surface
case専用mode
```

---

## 8. 実行確認

### py_compile

```bash
python -m py_compile \
  services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py \
  services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py \
  services/ai_inference/emlis_ai_public_feedback_meta.py \
  services/ai_inference/emlis_ai_reply_service.py
```

結果:

```text
passed
```

### display contract

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/test_emlis_ai_display_contract.py
```

結果:

```text
4 passed / 1 failed
```

残赤:

```text
RED-DC-002 only
```

### focused subset

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

### API public contract / two-stage reception

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/contract/test_emlis_ai_contracts.py \
  tests/test_emotion_submit_two_stage_reception_e2e.py
```

結果:

```text
10 passed, 3 warnings
```

---

## 9. 未確認

```text
- R7としてのdisplay contract test semantic再構成。
- RED-DC-002を、test期待更新として扱うかruntime lane修正として扱うかの最終判断。
- full backend suite green。
- P5 human Blind QA。
- P6 limited human readfeel review。
- 実機modal読感確認。
```

---

## 10. 次に進む場合の推奨

次は、R4へ進む前に、今回追加したlineage語彙がpublic metaに出る範囲をもう一度確認するのがよい。

その後の順番は次。

```text
R4: body-free lineage record builder / sanitizer方針の追加固定
R5: RED-DC-001 original source lineage mismatch分類・修正結果の確定
R6: RED-DC-002 pre-connection recovery lane mismatch分類・修正方針
R7: display contract test再構成
```

華恋の意見として、今回RED-DC-002を無理にgreenにしなかった判断は大事だった。  
Cocolonとして守りたいのは「赤を消した事実」ではなく、「どのsourceのsurfaceを人間が読むのかを嘘なく説明できること」だから。  

R2/R3でやるべきことは、final labelledをcomplete_initialへ偽装することではなく、complete_initialをpre-public / attemptedとして残し、final labelledをfinalとして明示することだった。今回の実装はその方向に合わせている。
